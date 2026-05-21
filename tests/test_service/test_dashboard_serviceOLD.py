from app.data import repository
import pytest
from app.services.dashboard_service import DashboardService
from app.data.repository import DashboardRepository

class MockRepository:
    def get_dashboard_data(self):
        return [
            {'id': 1, 'name': 'Revenue', 'value': '1000'},
            {'id': 2, 'name': 'Expenses', 'value': '500'}
        ]
        
@pytest.fixture
def service():
    repository = MockRepository()
    return DashboardService(repository)

def test_get_dashboard_data(service):
    data = service.get_dashboard_data()
    assert len(data) == 2
    assert data[0]['name'] == 'Revenue'
    assert data[0]['value'] == '1000'
    assert data[1]['name'] == 'Expenses'
    assert data[1]['value'] == '500'

