import datetime
import re

import sklearn.gaussian_process as gp
import numpy as np
import random
# from skopt.acquisition import gaussian_ei
from acqstion import gaussian_ei, gaussian_pi, gaussian_lcb
import matplotlib.pyplot as plt
import time
import requests
import sys
import csv
import logging,subprocess

logging.basicConfig(level=logging.INFO)

####################
np.random.seed(42)

kernel = gp.kernels.Matern()

previous_time=time.time()
previous_requests=0

filter = ""
splitter = ""

bal_file = "h1_h1_passthrough.balx"

if (bal_file == "h1_transformation.balx"):
    filter = "response_time_seconds(?:_mean|_stdDev|{).*transformationService\$\$service\$0.*timeWindow=\"60000\".*(?:quantile=\"0.999\"|quantile=\"0.99\"|,}).*"
    throughput_filter = "http_requests_total_value.*transformationService\$\$service\$0.*"
    splitter = "{protocol=\"http\",http_method=\"POST\",resource=\"transform\",http_url=\"/transform\",service=\"transformationService$$service$0\","
elif (bal_file == "h1_h1_passthrough.balx"):
    filter = "response_time_seconds(?:_mean|_stdDev|{).*passthroughService\$\$service\$0.*timeWindow=\"60000\".*(?:quantile=\"0.999\"|quantile=\"0.99\"|,}).*"
    throughput_filter = "http_requests_total_value.*passthroughService\$\$service\$0.*"
    #     splitter = "{protocol=\"http\",http_method=\"POST\",service=\"passthroughService$$service$0\",http_url=\"/passthrough\",http_status_code=\"200\",resource=\"passthrough\","
    splitter = "{protocol=\"http\",http_method=\"POST\",service=\"passthroughService$$service$0\",http_url=\"/passthrough\",resource=\"passthrough\","
elif (bal_file=="ballerina-echo.bal"):
    filter = "response_time_seconds(?:_mean|_stdDev|{).*EchoService\$\$service\$0.*timeWindow=\"60000\".*(?:quantile=\"0.999\"|quantile=\"0.99\"|,}).*"
    throughput_filter = "http_requests_total_value.*EchoService\$\$service\$0.*"
    splitter = "{http_url=\"/service/EchoService\",protocol=\"http\",http_method=\"POST\",resource=\"helloResource\",service=\"EchoService$$service$0\","


def get_performance(x_pass, loc):
    global data

    # requests.put("http://192.168.32.2:8080/setThreadPoolNetty?size=" + str(x_pass[0], x_pass[1]))
    subprocess.call(['java', '-jar', 'MBean.jar', 'set', str(x_pass[0])])
    subprocess.call(['ssh', 'netty', 'java', '-jar', '~/auto-tuning/MBean.jar', 'set', str(x_pass[1])])

    # time.sleep((loc + 1) * tuning_interval + start_time - time.time())
    time.sleep(60)
    # res = requests.get("http://192.168.32.2:8080/performance-netty").json()

    # data.append(res)
    # logging.info("99th Percentile :" + str(res[3]))
    # return float(res[3])
    res = query_metrics()
    print(res)

    data.append(res)
    print("Mean 99th per : " + str(res["99per"]), "\n")
    # logging.info("Mean 99th per : %s" + str(res["99per"]))
    return float(res["99per"])

def get_initial_points():
    iter_num = int(np.sqrt(number_of_initial_points))
    x_temp = []
    for i in range(0, iter_num + 1):
        x1 = thread_pool_min + i * (thread_pool_max - thread_pool_min) / iter_num
        for j in range(0, iter_num + 1):
            x2 = thread_pool_min + j * (thread_pool_max - thread_pool_min) / iter_num
            x_temp.append(int(x1))
            x_temp.append(int(x2))
            x_data.append(x_temp)
            y_data.append(get_performance(x_temp, i))
            param_history.append(x_temp)
            x_temp = []

def gausian_model(kern, xx, yy):
    model = gp.GaussianProcessRegressor(kernel=kern, alpha=noise_level,
                                        n_restarts_optimizer=10, normalize_y=True)

    model.fit(xx, yy)

    return model

def query_metrics():
    metrics_array = {
        "requests": 0,
        "throughput": 0,
        "mean": 0,
        "std_dev": 0,
        "99per": 0,
    }
    try:
        global previous_time
        global previous_requests

        URL = "http://127.0.0.1:9797/metrics"

        current_time = time.time()

        # sending get request and saving the response as response object
        r = requests.get(url=URL)

        data = r.text
        data_list = data.split("\n")



        # print(data)
        for line in data_list:
            try:
                x = re.findall(
                    filter,
                    line)

                throughput = re.findall(throughput_filter, line)
                if (throughput):

                    current_requests = float((throughput[0].split(" "))[1])

                    metrics_array["requests"] = current_requests
                    throughput_calculated=(current_requests - previous_requests) / (
                                current_time - previous_time)

                    metrics_array["throughput"] = throughput_calculated

                    previous_requests = current_requests

                s = x

                if s:
                    y = s[0].split(" ")
                    z = y[0].split(
                        splitter)

                    meanOrStd = z[0].split("response_time_seconds")
                    timeWindowAndQuantile = z[1].split("\"")

                    if (meanOrStd[1] == ''):
                        if (timeWindowAndQuantile[3] == "0.99"):
                            metrics_array["99per"] = float(y[1])*1000

                    elif (meanOrStd[1] == "_mean"):
                        metrics_array["mean"] = float(y[1])*1000

                    elif (meanOrStd[1] == "_stdDev"):
                        metrics_array["std_dev"] = float(y[1])*1000

            except Exception as e:
                pass

        previous_time = current_time

    except Exception as e:
        pass
    return metrics_array


# folder_name = sys.argv[1] if sys.argv[1][-1] == "/" else sys.argv[1] + "/"
# case_name = sys.argv[2]
#
# ru = int(sys.argv[3])
# mi = int(sys.argv[4])
# rd = int(sys.argv[5])
# tuning_interval = int(sys.argv[6])

folder_name = "testingme/"
case_name = "oracle51"
ru = 0
mi = 3600
rd = 0
tuning_interval = 60

data = []
param_history = []
test_duration = ru + mi + rd
iterations = test_duration // tuning_interval

noise_level = 1e-6
number_of_initial_points = 4

x_data = []
y_data = []

start_time = time.time()

thread_pool_max = 200
thread_pool_min = 4


get_initial_points()

model = gausian_model(kernel, x_data, y_data)

xi = 0.1

# use bayesian optimization
iteration_start_num = int(pow((np.sqrt(number_of_initial_points) + 1), 2))
for i in range(iteration_start_num, iterations):
    minimum = min(y_data)
    minimum = np.array(minimum)
    x_location = y_data.index(min(y_data))
    max_expected_improvement = 0
    max_points = []

    logging.info("xi - %f", xi)
    logging.info("iter - %i", i)

    for pool_size_1 in range(thread_pool_min, thread_pool_max + 1):
        for pool_size_2 in range(thread_pool_min, thread_pool_max + 1):
            x = [pool_size_1, pool_size_2]
            x_val = [x]

            # may be add a condition to stop explorering the already expored locations
            ei = gaussian_ei(np.array(x_val).reshape(1, -1), model, minimum, xi)

            if ei > max_expected_improvement:
                max_expected_improvement = ei
                max_points = [x_val]

            elif ei == max_expected_improvement:
                max_points.append(x_val)

    if max_expected_improvement == 0:
        logging.info("WARN: Maximum expected improvement was 0. Most likely to pick a random point next")
        next_x = x_data[x_location]
        logging.info(next_x)
        xi = xi - xi / 10
        if xi < 0.00001:
            xi = 0
    else:
        # select the point with maximum expected improvement
        # if there're multiple points with same ei, chose randomly
        idx = random.randint(0, len(max_points) - 1)
        next_x = max_points[idx]
        next_x = next_x[0]
        xi = xi + xi / 8
        if xi > 0.01:
            xi = 0.01
        elif xi == 0:
            xi = 0.00002

    logging.info(next_x)

    param_history.append(next_x)
    next_y = get_performance(next_x, i)
    y_data.append(next_y)
    x_data.append(next_x)

    x_data_arr = np.array(x_data)
    y_data_arr = np.array(y_data)

    model = gausian_model(kernel, x_data, y_data_arr)

logging.info("minimum found : %f", min(y_data))

log_time = str(datetime.datetime.now()).replace(" ","_")

with open(folder_name + case_name + "/results"+log_time+".csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["stdDev", "Requests", "Throughput", "99per", "Mean"])
    for line in data:
        writer.writerow([v for v in line.values()])

with open(folder_name + case_name + "/param_history"+log_time+".csv", "w") as f:
    writer = csv.writer(f)
    for line in param_history:
        writer.writerow(line)