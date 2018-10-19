#!/bin/sh
set -e
cp=/bin/cp
./main.py
$cp output/dhcpd.conf /etc/dhcp/dhcpd.conf
$cp output/network.conf /etc/dnsmasq-sync/network.conf
$cp output/network-ptr.conf /etc/dnsmasq-sync/network-ptr.conf
pihole restartdns
systemctl restart dhcpd

