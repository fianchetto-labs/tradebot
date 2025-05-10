from fianchetto_tradebot.server.common.io.rate_limiter import API, RATE_LIMIT_OK, TOO_MANY_REQUESTS_STR, THRESHOLD_COUNT

DEFAULT_CUSTOMER_NAME = "customer1"

class TestRateLimiter:

    def test_single_request(self):
        service = API()
        assert service.execute_endpoint(DEFAULT_CUSTOMER_NAME) == RATE_LIMIT_OK

    def test_two_less_than_threshold_requests_ok(self):
        service = API()

        TestRateLimiter.run_requests_within_limits(service, THRESHOLD_COUNT-2)

        assert service.execute_endpoint(DEFAULT_CUSTOMER_NAME) == RATE_LIMIT_OK

    def test_one_over_threshold_is_error(self):
        service = API()

        TestRateLimiter.run_requests_within_limits(service, THRESHOLD_COUNT)

        assert service.execute_endpoint(DEFAULT_CUSTOMER_NAME) == TOO_MANY_REQUESTS_STR

    def test_many_request_from_different_clients(self):
        service = API()

        num_clients = 3
        request_count = THRESHOLD_COUNT

        threshold_count_range_value = num_clients * request_count + 1
        for i in range(1, threshold_count_range_value):
            assert service.execute_endpoint(DEFAULT_CUSTOMER_NAME + str(i % num_clients)) == RATE_LIMIT_OK

    def test_many_request_from_different_clients_error(self):
        service = API()

        ok_count = 0
        error_count = 0

        num_clients = 3
        request_count = THRESHOLD_COUNT + 1

        threshold_count_range_value = num_clients * request_count + 1
        for i in range(1, threshold_count_range_value):
            if service.execute_endpoint(DEFAULT_CUSTOMER_NAME + str(i % num_clients)) == RATE_LIMIT_OK:
                ok_count += 1
            else:
                error_count += 1

        assert ok_count == num_clients * THRESHOLD_COUNT
        assert error_count == num_clients

    @staticmethod
    def run_requests_within_limits(service, count, customer_name=DEFAULT_CUSTOMER_NAME):
        threshold_count_range_value = count + 1
        for i in range(1, threshold_count_range_value):
            assert service.execute_endpoint(customer_name) == RATE_LIMIT_OK