#!/bin/bash

while true; do

    rm -rf /tmp/*
    rm -rf /var/tmp/*
    rm -rf /var/log/*
    rm -rf /var/cache/*
    rm -rf /root/.cache/*
    rm -rf /home/$USER/.cache/*
    rm -rf /root/logs
    

    for i in {3600..1}; do
        echo -ne "Menunggu: $i detik\r"
        sleep 1
    done

done
