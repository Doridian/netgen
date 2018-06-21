#!/usr/bin/env python

from IPy import IP
from yaml import load as yaml_load
from jinja2 import Template, Environment, FileSystemLoader

environment = Environment(loader = FileSystemLoader('./templates'))
with open('network.yml', 'r') as stream:
	environment.globals = yaml_load(stream)

class IPSafeCls(IP):
	def __init__(self, raw):
		super().__init__(raw)
		if self.version() != 4:
			raise Exception('Only support IPv4')
		plen = self.prefixlen()
		if plen % 8 != 0 or plen >= 32:
			raise Exception('Only suppot /24 /16 /8 /0')
		self.netips = {}

	def getnetworkip(self, ipaddr):
		if isinstance(ipaddr, int):
			return self[ipaddr]
		if ipaddr in self.netips:
			return self.netips[ipaddr]
		accum = 0
		shiftl = 0
		for i in reversed(ipaddr.split('.')):
			accum += int(i, 10) << shiftl
			shiftl += 8
		res = self[accum]
		self.netips[ipaddr] = res
		return res

_ipSafeCache = {}
def getsafeip(raw):
	global _ipSafeCache
	if raw in _ipSafeCache:
		return _ipSafeCache[raw]
	ip = IPSafeCls(raw)
	_ipSafeCache[raw] = ip
	return ip

def getnetworkip(ipaddr, network):
	return getsafeip(network).getnetworkip(ipaddr)

# Converts the subnet to its .in-addr.arpa host
def format_arpa(network):
	netip = getsafeip(network)
	plen = netip.prefixlen()
	ipsplit = netip.strNormal(0).split('.')[(plen >> 3) - 1::-1]
	return '.'.join(ipsplit) + '.in-addr.arpa'
environment.filters['format_arpa'] = format_arpa

# Converts an IP so its sub-part of .in-addr.arpa (the part not included with format_arpa above)
def format_ptrip(ipaddr, network):
	plen = getsafeip(network).prefixlen()
	netip = getnetworkip(ipaddr, network)
	ipsplit = netip.strNormal(0).split('.')[:(plen >> 3) - 1:-1]
	return '.'.join(ipsplit)	
environment.filters['format_ptrip'] = format_ptrip

# Gets the "Base address" of a subnet, 192.168.5.0/24 -> 192.168.5.0
def format_baseaddr(network):
	return getsafeip(network).strNormal(0)
environment.filters['format_baseaddr'] = format_baseaddr

# Gets the netmask of a subnet, 192.168.5.0/24 -> 255.255.255.0
def format_netmask(network):
	return getsafeip(network).strNetmask()
environment.filters['format_netmask'] = format_netmask

# Gets the specified IP inside a network, 2.30 [192.168.0.0/16] -> 192.168.2.30
def format_ipaddr(ipaddr, network):
	return getnetworkip(ipaddr, network).strNormal(0)
environment.filters['format_ipaddr'] = format_ipaddr

# Converts a short-host into a full LAN hostname
def format_host(hostname, domain):
	if '.' in hostname:
		return hostname
	return '%s.%s' % (hostname, domain)
environment.filters['format_host'] = format_host

def render_template(name):
	template = environment.get_template(name)
	outstr = template.render()
	with open('output/%s' % name, 'w') as outf:
		outf.write(outstr)

render_template('dhcpd.conf')
render_template('network.zone')
render_template('network-ptr.zone')
