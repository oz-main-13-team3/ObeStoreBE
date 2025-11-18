#!/bin/bash

NODE_EXPORTER_URL="http://3.36.63.25:9100/metrics"

echo "===== CPU 사용률 ====="
CPU_LINES=$(curl -s $NODE_EXPORTER_URL | grep '^node_cpu_seconds_total' | grep -v '^#' | grep -v 'guest')
CPUS=$(echo "$CPU_LINES" | awk -F'cpu=' '{print $2}' | awk -F',' '{gsub(/"/,""); print $1}' | sort -u)

for CPU in $CPUS; do
    TOTAL=$(echo "$CPU_LINES" | awk -v cpu="$CPU" '$0 ~ ("cpu=" "\"" cpu "\"") {sum+=$2} END{print sum}')
    IDLE=$(echo "$CPU_LINES" | awk -v cpu="$CPU" '$0 ~ ("cpu=" "\"" cpu "\".*,mode=\"idle\"") {print $2}')
    USAGE=$(awk -v idle="$IDLE" -v total="$TOTAL" 'BEGIN {if(total>0) printf "%.2f", (1-idle/total)*100; else print 0}')
    echo "CPU \"$CPU\", 사용률: $USAGE%"
done


echo -e "\n===== 메모리 ====="
MEM_TOTAL=$(curl -s $NODE_EXPORTER_URL | grep '^node_memory_MemTotal_bytes' | awk '{print $2}')
MEM_AVAILABLE=$(curl -s $NODE_EXPORTER_URL | grep '^node_memory_MemAvailable_bytes' | awk '{print $2}')
MEM_USED=$(awk -v total="$MEM_TOTAL" -v avail="$MEM_AVAILABLE" 'BEGIN {print total-avail}')
MEM_PERCENT=$(awk -v used="$MEM_USED" -v total="$MEM_TOTAL" 'BEGIN {if(total>0) printf "%.2f", used/total*100; else print 0}')
echo "사용 중: $(awk -v used="$MEM_USED" 'BEGIN{printf "%.2f", used/1024/1024}') MB ($MEM_PERCENT%) / 총: $(awk -v total="$MEM_TOTAL" 'BEGIN{printf "%.2f", total/1024/1024}') MB"

echo -e "\n===== 디스크 ====="
DISK_TOTAL=$(df --total --block-size=1 | grep total | awk '{print $2}')
DISK_USED=$(df --total --block-size=1 | grep total | awk '{print $3}')
DISK_PERCENT=$(awk -v used="$DISK_USED" -v total="$DISK_TOTAL" 'BEGIN {if(total>0) printf "%.2f", used/total*100; else print 0}')
echo "사용 중: $(awk -v used="$DISK_USED" 'BEGIN{printf "%.2f", used/1024/1024/1024}') GB ($DISK_PERCENT%) / 총: $(awk -v total="$DISK_TOTAL" 'BEGIN{printf "%.2f", total/1024/1024/1024}') GB"

echo -e "\n===== 시스템 부하 ====="
LOAD=$(uptime | awk -F'load average: ' '{print $2}')
echo "1분: $(echo $LOAD | awk -F',' '{print $1}'), 5분: $(echo $LOAD | awk -F',' '{print $2}'), 15분: $(echo $LOAD | awk -F',' '{print $3}')"