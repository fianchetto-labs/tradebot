from datetime import datetime, timedelta

TOO_MANY_REQUESTS_STR = "Too many requests. Please slow down rate of requests"
RATE_LIMIT_OK = "Rate Limit within Threshold. Please proceed."

THRESHOLD = timedelta(seconds=2)
THRESHOLD_COUNT = 5


class API:
    def __init__(self):
        self.request_history: dict[str, list] = dict()

    def execute_endpoint(self, customer_name):
        output_str = None
        # rate limiting
        if not self.rate_limit_ok(customer_name):
            print(TOO_MANY_REQUESTS_STR)
            return TOO_MANY_REQUESTS_STR

        print(RATE_LIMIT_OK)
        return RATE_LIMIT_OK

    def rate_limit_ok(self, customer_name):
        current_time = datetime.now()

        if customer_name not in self.request_history:
            self.request_history[customer_name] = list()
        self.request_history[customer_name].append(current_time)

        timestamps_of_last_requests = self.request_history[customer_name]

        if len(timestamps_of_last_requests) <= THRESHOLD_COUNT:
            return True

        index = -1 * (THRESHOLD_COUNT + 1)
        fifth_to_last_item = timestamps_of_last_requests[index]
        time_delta = current_time - fifth_to_last_item

        if time_delta < THRESHOLD:
            return False
        return True


if __name__ == "__main__":
    pass