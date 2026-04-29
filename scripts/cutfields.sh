#!/usr/bin/env bash
# cutfields.sh — extract IP-based packet fields from a PCAP into a CSV.
#
# Edit the two values below, then run:
#   bash cutfields.sh
#
# The CSV produced here is the input to cleandata.py.

INPUT_PCAP="input.pcap"
OUTPUT_CSV="output.csv"

tshark -r "$INPUT_PCAP" -Y "ip" -T fields \
  -e frame.time_epoch \
  -e frame.len \
  -e frame.protocols \
  -e ip.src \
  -e ip.dst \
  -e ip.proto \
  -e tcp.srcport \
  -e tcp.dstport \
  -e tcp.flags \
  -e udp.srcport \
  -e udp.dstport \
  -e ntp.stratum \
  -e ntp.ppoll \
  -e ntp.precision \
  -e ntp.rootdelay \
  -e ntp.rootdispersion \
  -e ntp.refid \
  -e ntp.org \
  -e ntp.rec \
  -e ntp.xmt \
  -E header=y \
  -E separator=, \
  -E occurrence=f > "$OUTPUT_CSV"
