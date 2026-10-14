from __future__ import annotations

import io
import csv
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from scipy.io import loadmat
from scipy.optimize import minimize

from Identificacao import fopdt_degrau
from Integrante2_PID import identificacao, metrics, simulate_pade, tunings

DATA = Path(__file__).resolve().parents[1] / 'Pneumatico_G8.mat'
if not DATA.exists():
    DATA = DATA.parent.parent / 'Pneumatico_G8.mat'
_cache: dict[str, Any] = {}

app = FastAPI(title='Grupo 8 Dashboard', version='1.0.0')
STATIC = Path(__file__).resolve().parent / 'static'
TEMPLATE = Path(__file__).resolve().parent / 'templates' / 'index.html'
app.mount('/static', StaticFiles(directory=STATIC), name='static')


def _as_float_list(values: Any) -> list[float]:
    arr = np.real_if_close(np.asarray(values), tol=1000)
    if np.iscomplexobj(arr):
        arr = arr.real
    return [float(v) for v in np.asarray(arr, dtype=float).ravel().tolist()]


def _read_mat_bytes(payload: bytes) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    try:
        data = loadmat(io.BytesIO(payload), squeeze_me=True)
        t = np.asarray(data['t'], dtype=float).ravel()
        u = np.asarray(data['Degrau'], dtype=float).ravel()
        y = np.asarray(data['Saida'], dtype=float).ravel()
    except Exception as exc:  # pragma: no cover - defensive validation
        raise HTTPException(status_code=422, detail=f'Arquivo .mat inválido: {exc}') from exc
    if len(t) < 50 or not (len(t) == len(u) == len(y)):
        raise HTTPException(status_code=422, detail='MAT inválido: t, Degrau e Saida devem ter o mesmo tamanho.')
    if not np.all(np.isfinite(np.r_[t, u, y])) or not np.all(np.diff(t) > 0):
        raise HTTPException(status_code=422, detail='MAT inválido: valores devem ser finitos e o tempo crescente.')
    return t, u, y


def _compile_identification(t: np.ndarray, u: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    result, best, base = identificacao(t, u, y)
    y0 = float(base['y0'])
    du = float(base['du'])
    t0 = float(base['t0'])
    models: dict[str, dict[str, float]] = {}
    series: dict[str, list[float]] = {'time': _as_float_list(t), 'measured': _as_float_list(y)}

    for name, params in result.items():
        k = float(params['k'])
        tau = float(params['tau'])
        theta = float(params['theta'])
        models[name] = {'k': k, 'tau': tau, 'theta': theta, 'rmse': float(params['rmse'])}
        series[name] = _as_float_list(fopdt_degrau(t, k, tau, theta, du, t0, y0))

    best_ref = result[best]
    best_k = float(best_ref['k'])
    best_tau = float(best_ref['tau'])
    best_theta = float(best_ref['theta'])

    def objective(values: np.ndarray) -> float:
        kk, tt, th = values
        if tt <= 0 or th < 0:
            return 1e12
        return float(np.sqrt(np.mean((fopdt_degrau(t, kk, tt, th, du, t0, y0) - y) ** 2)))

    optimum = minimize(objective, np.array([best_k, best_tau, best_theta]), method='Nelder-Mead', options={'maxiter': 2000})
    k_opt, tau_opt, theta_opt = [float(v) for v in optimum.x]
    models['Ajuste fino'] = {'k': k_opt, 'tau': tau_opt, 'theta': theta_opt, 'rmse': float(objective(optimum.x))}
    series['Ajuste fino'] = _as_float_list(fopdt_degrau(t, k_opt, tau_opt, theta_opt, du, t0, y0))

    payload = {
        'models': models,
        'best': best,
        'base': {
            't0': float(base['t0']),
            'u0': float(base['u0']),
            'uf': float(base['uf']),
            'du': float(base['du']),
            'y0': float(base['y0']),
            'yf': float(base['yf']),
        },
        'dataset': DATA.name,
        'samples': int(len(t)),
        'series': series,
    }
    return payload


def _load_dataset_from_path(path: Path | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    target = path or DATA
    if not target.exists():
        raise HTTPException(status_code=404, detail='Dataset não encontrado.')
    if target.suffix.lower() != '.mat':
        raise HTTPException(status_code=422, detail='Dataset deve estar em formato .mat.')
    try:
        data = loadmat(target, squeeze_me=True)
        t = np.asarray(data['t'], dtype=float).ravel()
        u = np.asarray(data['Degrau'], dtype=float).ravel()
        y = np.asarray(data['Saida'], dtype=float).ravel()
    except Exception as exc:  # pragma: no cover - defensive validation
        raise HTTPException(status_code=422, detail=f'Arquivo inválido: {exc}') from exc
    if not np.all(np.isfinite(np.r_[t, u, y])) or not np.all(np.diff(t) > 0):
        raise HTTPException(status_code=422, detail='Dataset inválido: dados de entrada e saída não são finitos ou cronologicamente válidos.')
    return t, u, y


def _dataset_exists() -> bool:
    return DATA.exists() or bool(_cache)


def _current_dataset() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if 'dataset' in _cache:
        return _cache['dataset']
    if DATA.exists():
        return _load_dataset_from_path(DATA)
    raise HTTPException(status_code=404, detail='Dataset não carregado.')


def _simulate_method(method: str, setpoint: float | None, payload: dict[str, Any]) -> dict[str, Any]:
    t, u, y = _current_dataset()
    identification = _compile_identification(t, u, y)
    selected_model = payload.get('model', 'melhor')
    if selected_model == 'melhor':
        selected_model = identification['best']
    if selected_model not in identification['models']:
        raise HTTPException(status_code=422, detail=f'Modelo de identificação inválido: {selected_model}.')
    model = identification['models'][selected_model]
    k = float(model['k'])
    tau = float(model['tau'])
    theta = float(model['theta'])
    base = identification['base']
    target = float(base['yf']) if setpoint is None else float(setpoint)

    if method == 'Manual':
        kp = payload.get('kp')
        ti = payload.get('ti')
        td = payload.get('td')
        if kp is None or ti is None or td is None:
            raise HTTPException(status_code=422, detail='Para método Manual, envie kp, ti e td.')
        kp = float(kp)
        ti = float(ti)
        td = float(td)
        if kp <= 0 or ti <= 0 or td < 0:
            raise HTTPException(status_code=422, detail='kp, ti devem ser positivos e td não-negativo.')
        pid = {'Kp': kp, 'Ti': ti, 'Td': td}
    else:
        allowed = tunings(k, tau, theta)
        if method not in allowed:
            raise HTTPException(status_code=422, detail=f'Método inválido: {method}.')
        pid = allowed[method]

    duration = float(payload.get('duration', 400.0))
    dt = float(payload.get('dt', 0.2))
    if duration <= 0 or dt <= 0 or duration / dt > 40000:
        raise HTTPException(status_code=422, detail='Parâmetros de simulação inválidos.')

    time = np.arange(int(round(duration / dt)) + 1, dtype=float) * dt
    y0 = float(base['y0'])
    closed, stable, poles, closed_metrics = simulate_pade(k, tau, theta, pid, int(payload.get('pade', 5)), time, y0, target)
    equivalent_input_step = (target - y0) / k
    open_curve = y0 + k * equivalent_input_step * (1.0 - np.exp(-np.maximum(time - theta, 0.0) / tau))
    open_metrics = metrics(time, open_curve, y0, target)
    result = {
        'method': method,
        'stable': bool(stable),
        'pid': pid,
        'setpoint': target,
        'series': {
            'time': _as_float_list(time),
            'open': _as_float_list(open_curve),
            'closed': _as_float_list(closed),
        },
        'metrics_closed': {
            'subida': closed_metrics['tempo_subida_s'],
            'acomodacao': closed_metrics['tempo_acomodacao_s'],
            'overshoot': float(closed_metrics['overshoot_pct']),
            'erro_final': float(closed_metrics['erro_final_bar']),
        },
        'metrics_open': {
            'subida': open_metrics['tempo_subida_s'],
            'acomodacao': open_metrics['tempo_acomodacao_s'],
            'overshoot': float(open_metrics['overshoot_pct']),
            'erro_final': float(open_metrics['erro_final_bar']),
        },
        'poles': _as_float_list(poles),
    }
    return result


@app.get('/')
def root() -> HTMLResponse:
    return HTMLResponse(content=TEMPLATE.read_text(encoding='utf-8'))


@app.get('/api/status')
def api_status() -> JSONResponse:
    dataset_loaded = DATA.exists() or bool(_cache)
    return JSONResponse({'dataset': dataset_loaded, 'path': str(DATA) if DATA.exists() else None})


@app.post('/api/dataset')
async def api_dataset(request: Request) -> JSONResponse:
    body = await request.body()
    if not body:
        raise HTTPException(status_code=422, detail='Nenhum conteúdo enviado.')
    t, u, y = _read_mat_bytes(body)
    _cache['dataset'] = (t, u, y)
    return JSONResponse({'ok': True, 'samples': int(len(t)), 'path': str(DATA)})


@app.get('/api/identification')
def api_identification() -> JSONResponse:
    if not _dataset_exists():
        raise HTTPException(status_code=404, detail='Dataset não carregado.')
    t, u, y = _current_dataset()
    payload = _compile_identification(t, u, y)
    return JSONResponse(payload)


@app.post('/api/simulate')
async def api_simulate(request: Request) -> JSONResponse:
    if not _dataset_exists():
        raise HTTPException(status_code=404, detail='Dataset não carregado.')
    payload = await request.json()
    method = str(payload.get('method', 'CHR 20%'))
    setpoint = payload.get('setpoint')
    result = _simulate_method(method, setpoint, payload)
    return JSONResponse(result)


@app.get('/api/compare')
def api_compare(
    model: str = 'melhor',
    setpoint: float | None = None,
    duration: float = 400.0,
    dt: float = 0.5,
    pade: int = 5,
) -> JSONResponse:
    if not _dataset_exists():
        raise HTTPException(status_code=404, detail='Dataset não carregado.')
    if not np.isfinite([duration, dt]).all() or duration <= 0 or dt <= 0 or duration / dt > 40000:
        raise HTTPException(status_code=422, detail='Parâmetros de simulação inválidos.')
    t, u, y = _current_dataset()
    info = _compile_identification(t, u, y)
    target = float(info['base']['yf']) if setpoint is None else setpoint
    runs = []
    for method in ['CHR 20%', 'Cohen-Coon']:
        result = _simulate_method(method, target, {
            'model': model,
            'duration': duration,
            'dt': dt,
            'pade': pade,
        })
        runs.append({
            'method': method,
            'pid': result['pid'],
            'series': result['series'],
            'metrics_closed': result['metrics_closed'],
            'stable': result['stable'],
        })

    winner_rise = min(runs, key=lambda item: (item['metrics_closed']['subida'] is None, item['metrics_closed']['subida'] if item['metrics_closed']['subida'] is not None else float('inf')))
    winner_settle = min(runs, key=lambda item: (item['metrics_closed']['acomodacao'] is None, item['metrics_closed']['acomodacao'] if item['metrics_closed']['acomodacao'] is not None else float('inf')))

    return JSONResponse({
        'runs': runs,
        'winner_rise': winner_rise['method'],
        'winner_settle': winner_settle['method'],
        'setpoint': target,
    })


@app.post('/api/export/csv')
async def export_csv(request: Request) -> Response:
    if not _dataset_exists():
        raise HTTPException(status_code=404, detail='Dataset não carregado.')
    payload = await request.json()
    result = _simulate_method(str(payload.get('method', 'CHR 20%')), payload.get('setpoint'), payload)
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['tempo_s', 'malha_aberta', 'malha_fechada', 'setpoint'])
    writer.writerows(zip(
        result['series']['time'],
        result['series']['open'],
        result['series']['closed'],
        [result['setpoint']] * len(result['series']['time']),
    ))
    return Response(
        content=output.getvalue(),
        media_type='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename="grafico_pid_g8.csv"'},
    )


@app.post('/api/export/png')
async def export_png(request: Request) -> Response:
    if not _dataset_exists():
        raise HTTPException(status_code=404, detail='Dataset não carregado.')
    payload = await request.json()
    result = _simulate_method(str(payload.get('method', 'CHR 20%')), payload.get('setpoint'), payload)
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    figure = Figure(figsize=(11, 5.5), dpi=160)
    axis = figure.subplots()
    time = result['series']['time']
    axis.plot(time, result['series']['open'], label='Malha aberta', linewidth=1.7)
    axis.plot(time, result['series']['closed'], label='Malha fechada', linewidth=1.7)
    axis.axhline(result['setpoint'], color='#b59b46', linestyle='--', label='SetPoint')
    axis.set(xlabel='Tempo (s)', ylabel='Saída', title='Resposta temporal do controle PID — Grupo 8')
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    image = io.BytesIO()
    FigureCanvasAgg(figure).print_png(image)
    return Response(
        content=image.getvalue(),
        media_type='image/png',
        headers={'Content-Disposition': 'attachment; filename="grafico_pid_g8.png"'},
    )
