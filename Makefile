.PHONY: test test-unit test-integration test-bench coverage

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-bench:
	pytest tests/benchmarks/ --benchmark-only --benchmark-autosave

coverage:
	pytest tests/unit/ tests/integration/ \
	    --cov=app --cov-report=term-missing --cov-report=html:htmlcov
