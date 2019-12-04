#!/usr/bin/env bash
#default innodb_buffer_pool_size=134217728
#default innodb_thread_sleep_delay=10000
#echo "setting innodb_buffer_pool_size=${1}"
#mysql -u root -proot -e "set global innodb_buffer_pool_size=${1};"
#sleep 1
#array=();
#while read -a row;
#do
#   array=${row[1]};
#done < <(echo "show variables like 'innodb_buffer_pool_size';" | mysql -u root -proot);
#echo 'innodb_buffer_pool_size = '${array};
echo "setting innodb_thread_sleep_delay=${1}"
mysql -u root -proot -e "set global innodb_thread_sleep_delay=${1};"
sleep 1
array=();
while read -a row;
do
   array=${row[1]};
done < <(echo "show variables like 'innodb_thread_sleep_delay';" | mysql -u root -proot);
echo 'innodb_thread_sleep_delay = '${array};
