#!/usr/bin/env bash
nohup java -jar ~/LocalBuildBallerinaPerformanceTest/performanceCommon/performance-common/components/netty-http-echo-service/target/netty-http-echo-service-0.3.1-SNAPSHOT.jar &

nohup /home/aathmsn/Downloads/Compressed/Test/ballerina-0.990.2-SNAPSHOT/bin/ballerina run -e b7a.runtime.scheduler.corepoolsize=25 -e b7a.runtime.scheduler.maxpoolsize=200 -e b7a.runtime.scheduler.queuetype=default-linked -e b7a.runtime.scheduler.keepalivetime=10 --observe ~/LocalBuildBallerinaPerformanceTest/extracted\ from\ the\ zip/ballerina/bal/h1c_h1c_passthrough.bal &

cd ~/Downloads/apache-jmeter-5.1.1/bin
nohup ./jmeter -n -t SequentialTest.jmx &

sleep 20
cd ~/IdeaProjects/netty-performace-tuning/
python bayesian_both.py 
