import subprocess
import sklearn.gaussian_process as gp
import numpy as np
import random
# from skopt.acquisition import gaussian_ei
from acqstion import gaussian_ei, gaussian_pi, gaussian_lcb
import matplotlib.pyplot as plt
import time,datetime
import requests
import sys
import csv
import logging,re

#from bayesian_optimization_util import plot_approximation, plot_acquisition

logging.basicConfig(level=logging.INFO)

####################
bounds = np.array([[4, 201]])

np.random.seed(42)

kernel = gp.kernels.Matern()

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


def function(X):
    #return np.sin(X / 5.0) * X
    return -1.0*np.sin(X/10.0)*X


def initial_plot():
    global X_plot_data
    X_plot_data = np.arange(bounds[:, 0], bounds[:, 1], 1).reshape(-1, 1)
    global Y_plot_data
    Y_plot_data = function(X_plot_data)

    plt.plot(X_plot_data, Y_plot_data, lw=2, label='Noise-free objective')
    plt.legend()
    plt.show()
########################

def _normalize(x, minimum, maximum):
    return (x - minimum) / (maximum - minimum)


def get_performance(x_pass, lower_bound, loc, online_check):
    global data

    if online_check:
        # requests.put("http://127.0.0.1:8080/setThreadPoolNetty?size=" + str(x_pass[0]))
        subprocess.call(['java', '-jar', 'MBean.jar', 'set', str(x_pass[0])])
        subprocess.call(['ssh','netty','java', '-jar', '~/auto-tuning/MBean.jar', 'set', str(x_pass[1])])

        time.sleep((loc + 1) * tuning_interval + start_time - time.time())
        # time.sleep(2)

        #res = requests.get("http://127.0.0.1:8080/performance-netty").json()
        res=query_metrics()
        print(res)

        data.append(res)
        print("Mean 99th per : " + str(res["99per"]),"\n")
        # logging.info("Mean 99th per : %s" + str(res["99per"]))
        return float(res["99per"])

    else:
        noise_loc = np.random.randint(0, 19)
        x_data_loc = np.where(X_plot_data == x_pass)
        return_val = Y_plot_data[x_data_loc] + noise_dist[noise_loc]
        #return_val = Y_plot_data[x_data_loc]
        return return_val

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
        resp = requests.get(url=URL)

        data = resp.text
        data_list = data.split("\n")

        for line in data_list:
            try:
                filtered_output = re.findall(
                    filter,
                    line)

                throughput = re.findall(throughput_filter, line)
                if (throughput):
                    current_requests = float((throughput[0].split(" "))[1])

                    metrics_array["requests"] = current_requests
                    throughput_calculated = (current_requests - previous_requests) / (
                            current_time - previous_time)

                    metrics_array["throughput"] = throughput_calculated

                    previous_requests = current_requests

                filtered_output_copy = filtered_output

                if filtered_output_copy:
                    first_split = filtered_output_copy[0].split(" ")
                    final_split = first_split[0].split(
                        splitter)

                    meanOrStd = final_split[0].split("response_time_seconds")
                    timeWindowAndQuantile = final_split[1].split("\"")

                    if (meanOrStd[1] == ''):
                        if (timeWindowAndQuantile[3] == "0.99"):
                            metrics_array["99per"] = float(y[1]) * 1000

                    elif (meanOrStd[1] == "_mean"):
                        metrics_array["mean"] = float(first_split[1]) * 1000

                    elif (meanOrStd[1] == "_stdDev"):
                        metrics_array["std_dev"] = float(first_split[1]) * 1000

            except Exception as e:
                pass

        previous_time = current_time

    except Exception as e:
        pass
    return metrics_array


def get_initial_points():
    for i in range(0, number_of_initial_points+1):
        x_ballerina = thread_pool_min + i * (thread_pool_max - thread_pool_min) / number_of_initial_points
        x_ballerina = int(x_ballerina)
        logging.info('X = %i',x_ballerina)

        x_netty = thread_pool_min + i * (thread_pool_max - thread_pool_min) / number_of_initial_points
        x_netty = int(x_netty)
        logging.info('X = %i', x_netty)

        x_data.append([x_ballerina,x_netty])
        y_data.append(get_performance([x_ballerina,x_netty], thread_pool_min, i, online))
        param_history.append([x_ballerina,x_netty])


def data_plot():
    #plot_approximation(model, X_plot_data, Y_plot_data, param_history, y_data, next_x, show_legend=i == 0)
    plt.title('Iteration {i + 1}')
    plt.show(block=False)
    plt.pause(0.5)
    plt.close()

def gausian_model(kern, xx, yy):
    model = gp.GaussianProcessRegressor(kernel=kern, alpha=noise_level,
                                        n_restarts_optimizer=10, normalize_y=True)

    model.fit(xx, yy)

    return model

#check_srt = sys.argv[7]
check_srt = True
online = True if check_srt == True else False

if online:
    # folder_name = sys.argv[1] if sys.argv[1][-1] == "/" else sys.argv[1] + "/"
    # case_name = sys.argv[2]

    # ru = int(sys.argv[3])
    # mi = int(sys.argv[4])
    # rd = int(sys.argv[5])
    #tuning_interval = int(sys.argv[6])
    folder_name = "test-results/"
    case_name = "passthrough"
    ru = 0
    mi = 3600
    rd = 0
    tuning_interval = 60

else:
    ru = 0
    mi = 1000
    rd = 0
    tuning_interval = 10

data = []
X_plot_data = []
Y_plot_data = []
param_history = []
test_duration = ru + mi + rd
iterations = test_duration // tuning_interval

noise_level = 1e-6
number_of_initial_points = 8 #4


x_data = []
y_data = []

start_time = time.time()

thread_pool_max = 200
thread_pool_min = 4

previous_time=time.time()
previous_requests=0


if not online:
    noise_dist = np.random.normal(0, 5, 20)
    initial_plot()

get_initial_points()

model = gausian_model(kernel, x_data, y_data)

xi = 0.1

# use bayesian optimization
for i in range(number_of_initial_points+1, iterations):
    minimum = min(y_data)
    x_location = y_data.index(min(y_data))
    max_expected_improvement = 0
    max_points = []
    max_points_unnormalized = []

    print("xi - ", xi)
    # logging.info("xi - %f", xi)
    print("iter - ", i)
    # logging.info("iter - %i", i)

    for pool_size in range(thread_pool_min, thread_pool_max + 1):
        for pool_size2 in range(thread_pool_min, thread_pool_max + 1):
            x = [pool_size,pool_size2]
            x_val = [x[0],x[1]]

            # may be add a condition to stop explorering the already expored locations
            ei = gaussian_ei(np.array(x_val).reshape(1, -1), model, minimum, xi)


            if ei > max_expected_improvement:
                max_expected_improvement = ei
                max_points = [x_val]

            elif ei == max_expected_improvement:
                max_points.append(x_val)

    if max_expected_improvement == 0:
        print("WARN: Maximum expected improvement was 0. Most likely to pick a random point next")
        # logging.info("WARN: Maximum expected improvement was 0. Most likely to pick a random point next")
        next_x = x_data[x_location]

        # logging.info(next_x)
        xi = xi - xi / 10
        if xi < 0.00001:
            xi = 0
    else:
        # select the point with maximum expected improvement
        # if there're multiple points with same ei, chose randomly
        idx = random.randint(0, len(max_points) - 1)
        next_x = max_points[idx]
        xi = xi + xi / 8
        if xi > 0.01:
            xi = 0.01
        elif xi == 0:
            xi = 0.00002
    print(next_x)

    param_history.append(next_x)
    next_y = get_performance(next_x, thread_pool_min, i, online)
    y_data.append(next_y)
    x_data.append(next_x)

    x_data_arr = np.array(x_data)
    y_data_arr = np.array(y_data)

    model = gausian_model(kernel, x_data, y_data_arr)

    if not online:
        data_plot()

print("minimum found : ", min(y_data))
# logging.info("minimum found : %f", min(y_data))

if online:

    log_time = str(datetime.datetime.now()).replace(" ","_")

    with open(folder_name + case_name + "/results" + log_time + ".csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["stdDev", "Requests", "Throughput", "99per", "Mean"])
        for line in data:
            writer.writerow([v for v in line.values()])

    with open(folder_name + case_name + "/param_history" + log_time + ".csv", "w") as f:
        writer = csv.writer(f)
        for line in param_history:
            writer.writerow(line)
