"""Optional queue adapter placeholder (RQ/Celery)"""
def enqueue(task, *args, **kwargs):
    # Hook into a real queue in production
    print(f"enqueue placeholder: {task}")
