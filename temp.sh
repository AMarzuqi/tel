#!/bin/bash

while true; do
    echo "Menghapus file sementara..."
    rm -rf /tmp/*
    rm -rf /var/tmp/*
    rm -rf /var/log/*
    rm -rf /var/cache/*
    rm -rf /root/.cache/*
    rm -rf /home/$USER/.cache/*
    rm -rf /root/logs


    
    echo "Pembersihan selesai. Menunggu 1 menit..."
    sleep 60  # Tunggu 60 detik sebelum menjalankan ulang
done
