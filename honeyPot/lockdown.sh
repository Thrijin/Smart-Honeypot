#!/bin/bash
ATTACKER=192.168.56.102
HOSTONLY=192.168.56.1

sudo iptables -F
sudo iptables -X
sudo iptables -t nat -F
sudo iptables -P INPUT DROP
sudo iptables -P OUTPUT DROP
sudo iptables -P FORWARD DROP

# allow loopback
sudo iptables -A INPUT -i lo -j ACCEPT
sudo iptables -A OUTPUT -o lo -j ACCEPT

# allow established
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# allow attacker -> flask(8080) and ssh(22)
sudo iptables -A INPUT -p tcp -s $ATTACKER --dport 8080 -m conntrack --ctstate NEW -j ACCEPT
sudo iptables -A INPUT -p tcp -s $ATTACKER --dport 22 -m conntrack --ctstate NEW -j ACCEPT

# allow honeypot outbound to attacker for replies
sudo iptables -A OUTPUT -p tcp -d $ATTACKER --sport 8080 -m conntrack --ctstate ESTABLISHED -j ACCEPT
sudo iptables -A OUTPUT -p tcp -d $ATTACKER --sport 22 -m conntrack --ctstate ESTABLISHED -j ACCEPT

# allow host-only controller SSH (optional)
sudo iptables -A INPUT -p tcp -s $HOSTONLY --dport 22 -m conntrack --ctstate NEW -j ACCEPT
sudo iptables -A OUTPUT -p tcp -d $HOSTONLY --sport 22 -m conntrack --ctstate ESTABLISHED -j ACCEPT

sudo iptables -L -n -v
echo "Lockdown complete: only $ATTACKER and $HOSTONLY allowed."
