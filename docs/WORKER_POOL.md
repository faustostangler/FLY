# Worker Pool

The worker pool in `infrastructure.helpers.worker_pool.WorkerPool` wraps `ThreadPoolExecutor`.

```
ExecutionResultDTO = WorkerPool.run(tasks, processor, logger,
                                 on_result=None,
                                 post_callback=None)
```

- **tasks** – iterable of inputs.
- **processor** – function applied to each item.
- **on_result** – called for every processed item.
- **post_callback** – called once with the list of results after completion.

`WorkerPool` collects metrics for network and processing bytes and logs start and finish messages. The pool size defaults to `config.global_settings.max_workers`.
