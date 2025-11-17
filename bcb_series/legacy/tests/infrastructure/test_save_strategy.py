from infrastructure.helpers.save_strategy import SaveStrategy


def test_handle_flushes_on_threshold():
    collected = []

    def cb(buffer):
        collected.append(list(buffer))

    strategy = SaveStrategy(cb, threshold=2)
    strategy.handle(1)
    strategy.handle(2)

    assert collected == [[1, 2]]
    assert strategy.buffer == []


def test_handle_flushes_on_remaining():
    collected = []

    def cb(buffer):
        collected.append(list(buffer))

    strategy = SaveStrategy(cb, threshold=3)
    items = [1, 2, 3, 4, 5]
    for i, item in enumerate(items):
        remaining = len(items) - i - 1
        strategy.handle(item, remaining)

    assert collected == [[1, 2, 3], [4, 5]]
    assert strategy.buffer == []


def test_threshold_loaded_from_config():
    collected = []

    def cb(buffer):
        collected.append(list(buffer))

    class DummyConfig:
        class GlobalSettings:
            threshold = 2

        global_settings = GlobalSettings()

    strategy = SaveStrategy(cb, config=DummyConfig())
    strategy.handle(1)
    strategy.handle(2)

    assert collected == [[1, 2]]
    assert strategy.buffer == []


def test_handle_accepts_iterable():
    """Items provided as an iterable should be buffered individually."""

    collected = []

    def cb(buffer):
        collected.append(list(buffer))

    strategy = SaveStrategy(cb, threshold=4)
    strategy.handle([1, 2])
    strategy.handle([3, 4])
    strategy.finalize()

    assert collected == [[[1, 2], [3, 4]]]
    assert strategy.buffer == []
