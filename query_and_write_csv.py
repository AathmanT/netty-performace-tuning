import time
import requests
import csv
import re

folder_name = "testingme/"
case_name = "query"

data = []

log_time=str(time.time())

previous_time = time.time()
previous_requests = 0

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
elif (bal_file == "ballerina-echo.bal"):
    filter = "response_time_seconds(?:_mean|_stdDev|{).*EchoService\$\$service\$0.*timeWindow=\"60000\".*(?:quantile=\"0.999\"|quantile=\"0.99\"|,}).*"
    throughput_filter = "http_requests_total_value.*EchoService\$\$service\$0.*"
    splitter = "{http_url=\"/service/EchoService\",protocol=\"http\",http_method=\"POST\",resource=\"helloResource\",service=\"EchoService$$service$0\","


def query_metrics():
    try:
        global previous_time
        global previous_requests

        URL = "http://127.0.0.1:9797/metrics"

        current_time = time.time()

        # sending get request and saving the response as response object
        r = requests.get(url=URL)

        data = r.text
        data_list = data.split("\n")

        metrics_array = {
            "requests": 0,
            "throughput": 0,
            "mean": 0,
            "std_dev": 0,
            "99per": 0,
        }

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
                    throughput_calculated = (current_requests - previous_requests) / (
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
                            metrics_array["99per"] = float(y[1]) * 1000

                    elif (meanOrStd[1] == "_mean"):
                        metrics_array["mean"] = float(y[1]) * 1000

                    elif (meanOrStd[1] == "_stdDev"):
                        metrics_array["std_dev"] = float(y[1]) * 1000

            except Exception as e:
                pass

        previous_time = current_time

    except Exception as e:
        pass
    return metrics_array


def write_csv():
    with open(folder_name + case_name + "/results"+log_time+".csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["stdDev", "Requests", "Throughput", "99per", "Mean"])
        for line in data:
            writer.writerow([v for v in line.values()])

for i in range(50):
    time.sleep(60)
    res = query_metrics()
    print(res)
    data.append(res)
write_csv()