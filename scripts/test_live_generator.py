from database import (
    DataRepository,
    create_database_engine,
)
from simulation.live_activity_generator import (
    LiveActivityGenerator,
)

repository = DataRepository(
    create_database_engine()
)

employees = repository.read_table(
    repository.EMPLOYEES_TABLE
)

generator = LiveActivityGenerator()

activity = generator.generate(
    employees=employees,
    starting_id=repository.get_last_activity_id() + 1,
    activity_count=1,
)

print(activity)