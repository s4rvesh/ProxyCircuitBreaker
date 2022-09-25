from datetime import datetime
from states import States
import functools
import json
import requests
import socket
from requests.models import Response
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


# Circuit breaker class
class CircuitBreaker:
    def __init__(self, exceptions, max_failure_count, reset_timeout, call_timeout):
        # method which makes the call
        # exceptions to catch
        self.exceptions = exceptions
        # number of tries before state changes to open_state
        self.max_failure_count = max_failure_count
        # delay between closed_state and half_open_state
        self.reset_timeout = reset_timeout
        self.call_timeout = call_timeout
        self.latest_timestamp = None
        # default state of a circuit breaker (closed_state)
        self.state = States.CLOSED
        # failed count
        self.failed_count = 0

    # set current state in the circuit breaker
    def set_state(self, state):
        old_state = self.state
        self.state = state
        print("State changed from {} to {}".format(old_state, self.state))

    # handle closed_state in a circuit breaker
    def handle_closed_state(self, *args):
        exceptions = self.exceptions
        try:
            response = self.make_request(*args)
            print("In Closed state")
            print(response)
            # print(self.remote_call_method)
            print("Success")
            # update latest_timestamp after call succeed
            self.latest_timestamp = datetime.utcnow().timestamp()
            return response
        except socket.timeout as exception:
            print(exception)
            print("Failure Timeout")
            # call failure increases the failure_count
            self.failed_count += 1
            # update latest_timestamp
            self.latest_timestamp = datetime.utcnow().timestamp()
            # if failed counter reaches max_failure_count, breaker is tripped into open_state
            if self.failed_count >= self.max_failure_count:
                self.set_state(States.OPEN)
            raise exception
        except exceptions as exception:
            print(exception)
            print("Failure")
            # call failure increases the failure_count
            self.failed_count += 1
            # update latest_timestamp
            self.latest_timestamp = datetime.utcnow().timestamp()
            # if failed counter reaches max_failure_count, breaker is tripped into open_state
            if self.failed_count >= self.max_failure_count:
                self.set_state(States.OPEN)
            raise exception

    # handle open_state in a circuit breaker
    def handle_open_state(self, *args):
        current_time = datetime.utcnow().timestamp()
        last_timestamp_and_delay = self.latest_timestamp + self.reset_timeout
        # if reset_timeout is not elapsed since last call, return the response
        if last_timestamp_and_delay >= current_time:
            msg = "Retry after {} secs".format(last_timestamp_and_delay - current_time)
            the_response = Response()
            the_response.code = 503
            the_response._content = msg.encode()

            return the_response

        # if reset_timeout is elapsed since last call, call is made to the failing service
        # update the circuit state to half_open_state
        self.set_state(States.HALF_OPEN)
        exceptions = self.exceptions
        try:
            response = self.make_request(*args)
            # success call resets the breaker to closed_state
            self.set_state(States.CLOSED)
            # reset failed_count
            self.failed_count = 0
            # update latest_timestamp after call succeed
            self.latest_timestamp = datetime.utcnow().timestamp()
            return response
        except socket.timeout as exception:
            # call failure increases the failed_count
            self.failed_count += 1
            print("State open, failed count: " + str(self.failed_count))
            # update latest_timestamp
            self.latest_timestamp = datetime.utcnow().timestamp()
            # on call failure, breaker is tripped again into open_state
            self.set_state(States.OPEN)
            raise exception
        except exceptions as exception:
            # call failure increases the failed_count
            self.failed_count += 1
            print("State open, failed count: " + str(self.failed_count))
            # update latest_timestamp
            self.latest_timestamp = datetime.utcnow().timestamp()
            # on call failure, breaker is tripped again into open_state
            self.set_state(States.OPEN)
            raise exception

    # redirect call
    def redirect_call(self, *args):
        if self.state == States.CLOSED:
            return self.handle_closed_state(*args)
        elif self.state == States.OPEN:
            return self.handle_open_state(*args)

    # call method
    def make_request(self, url):
        try:
            req = Request(url)
            res = urlopen(req, timeout=self.call_timeout)
            print(res.code)
            if res.code == 200:
                print(f"Call to {url} succeed with status code = {res.code}")
                return res
            if 500 <= res.code < 600:
                print(f"Call to {url} failed with status code = {res.code}")
                raise Exception("Server Issue")
        except socket.timeout as exception:
            print(f"Call to {url} failed due to Timeout")
            raise exception
        except Exception as exception:
            print(f"Call to {url} failed")
            raise exception
