import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'dashboard'))
import io
from pathlib import Path
import numpy as np
import pytest
from scipy.io import savemat
from fastapi.testclient import TestClient
import server

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DATA',tmp_path/'Pneumatico_G8.mat')
    server._cache.clear()
    return TestClient(server.app)

def dataset_bytes():
    t=np.linspace(0,400,2001)
    u=np.where(t>=5,50.,0.)
    y=1.1+0.1147*u*(1-np.exp(-np.maximum(t-5-14,0)/55))
    buf=io.BytesIO();savemat(buf,{'t':t,'Degrau':u,'Saida':y});return buf.getvalue()

def test_endpoints_and_upload(client):
    page=client.get('/')
    assert page.status_code==200
    assert 'id="pid"' in page.text and '/static/app.js' in page.text
    assert 'id="export-chart"' in page.text
    assert 'id="download-data"' in page.text
    assert client.get('/static/style.css').status_code==200
    assert client.get('/static/app.js').status_code==200
    assert client.get('/api/status').json()['dataset'] is False
    assert client.get('/api/identification').status_code==404
    r=client.post('/api/dataset',content=dataset_bytes()); assert r.status_code==200,r.text
    assert r.json()['samples']==2001
    info=client.get('/api/identification');assert info.status_code==200,info.text
    identification=info.json()
    assert identification['best'] in ['Smith','Sundaresan']
    assert len(identification['series']['time'])==2001
    r=client.post('/api/simulate',json={'method':'CHR 20%','setpoint':8});assert r.status_code==200,r.text
    assert r.json()['stable'] is True
    simulation=r.json()
    sample_index=200  # 40 s at the default 0.2 s sampling interval.
    selected=identification['models'][identification['best']]
    t40_theta=max(40-selected['theta'],0)
    expected_open=identification['base']['y0']+(8-identification['base']['y0'])*(1-np.exp(-t40_theta/selected['tau']))
    assert simulation['series']['open'][sample_index]==pytest.approx(expected_open)
    manual=client.post('/api/simulate',json={'method':'Manual','kp':20,'ti':60,'td':5,'setpoint':8});assert manual.status_code==200,manual.text
    comp=client.get('/api/compare');assert comp.status_code==200,comp.text
    assert len(comp.json()['runs'])==2
    comp=client.get('/api/compare?model=Sundaresan&duration=40&dt=0.5&pade=1&setpoint=8')
    assert comp.status_code==200,comp.text
    assert len(comp.json()['runs'][0]['series']['time'])==81
    csv_export=client.post('/api/export/csv',json={'method':'CHR 20%','setpoint':8})
    assert csv_export.status_code==200 and 'text/csv' in csv_export.headers['content-type']
    assert 'malha_fechada' in csv_export.text
    png_export=client.post('/api/export/png',json={'method':'CHR 20%','setpoint':8})
    assert png_export.status_code==200 and png_export.content.startswith(b'\x89PNG')

def test_invalid(client):
    assert client.post('/api/dataset',content=b'not a mat').status_code==422
    client.post('/api/dataset',content=dataset_bytes())
    assert client.post('/api/simulate',json={'method':'Manual'}).status_code==422
    assert client.post('/api/simulate',json={'method':'Manual','kp':-1,'ti':1,'td':1}).status_code==422
