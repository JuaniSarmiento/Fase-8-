import sys
sys.path.insert(0, '/app')

from backend.src_v3.infrastructure.persistence.sqlalchemy.models.activity_model import ActivityModel, ActivityStatus

try:
    a = ActivityModel(
        activity_id='test-123',
        title='Test Activity',
        description='Test description',
        instructions='Test instructions',
        module_id='module-123',
        teacher_id='teacher-123',
        order_index=0,
        policies={},
        status=ActivityStatus.ACTIVE
    )
    print('✅ ActivityModel created successfully')
    print(f'Has description attr: {hasattr(a, "description")}')
    print(f'Description value: {a.description}')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
