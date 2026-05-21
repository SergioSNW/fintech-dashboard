from app.data.repository import DashboardRepository

class DashboardService:
    def __init__(self):
        self.repository = DashboardRepository()

    def get_dashboard_data(self):
        # Fetch data from the repository
        return self.repository.get_dashboard_data()
        # Process data if needed (e.g., calculations, formatting)
        #processed_data = self.process_data(data)
        #return processed_data