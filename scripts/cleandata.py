import csv
import json

INPUT_CSV = "<filename>.csv"
OUTPUT_JSON = "<filename>.json"


def clean(v):
    if v is None:
        return None
    v = v.strip()
    if v == "" or v == "NULL":
        return None
    return v


def clean_protocols(proto_chain):
    if not proto_chain:
        return None, None, None, False

    raw_parts = proto_chain.split(":")

    # Anomalous signals
    raw_length = len(raw_parts)
    unique_count = len(set(raw_parts))

    # Detect excessive duplication
    duplication_ratio = unique_count / raw_length if raw_length > 0 else 1

    has_noise = any(p in ("x509sat", "x509ce", "pkix1implicit", "pkix1explicit") for p in raw_parts)

    # Flag anomaly conditions
    anomaly = (
        raw_length > 20 or            # very deep protocol chain
        duplication_ratio < 0.5 or    # lots of repeated layers
        has_noise                     # known TLS parsing spam
    )

    
    IGNORE = {
        "eth", "ethertype",
        "x509sat", "x509ce",
        "pkix1implicit", "pkix1explicit"
    }

    filtered = [p for p in raw_parts if p not in IGNORE]

    # Deduplicate while preserving order
    seen = set()
    stack = []
    for p in filtered:
        if p not in seen:
            seen.add(p)
            stack.append(p)

    # Cap depth
    stack = stack[:5]

    # Transport
    transport = None
    for p in stack:
        if p in ("tcp", "udp"):
            transport = p

    # Application
    application = None
    if stack:
        last = stack[-1]
        if last not in ("tcp", "udp", "ip"):
            application = last

    return stack, transport, application, anomaly

def main():
    output = []

    with open(INPUT_CSV, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:

            # Parse protocols
            proto_chain_raw = clean(row.get("frame.protocols"))

            stack, transport, application, anomaly = clean_protocols(proto_chain_raw)

            # Optional: cleaned version of protocol chain
            cleaned_proto_chain = ":".join(stack) if stack else proto_chain_raw

            # Build the packet
            packet = {
                "frame.time_epoch": clean(row.get("frame.time_epoch")),
                "frame.len": clean(row.get("frame.len")),

                # Keep BOTH raw and cleaned 
                "frame.protocols": proto_chain_raw,
                "frame.protocols_clean": cleaned_proto_chain,

                "protocol.stack": stack,
                "protocol.transport": transport,
                "protocol.application": application,

                "ip.src": clean(row.get("ip.src")),
                "ip.dst": clean(row.get("ip.dst")),
                "ip.proto": clean(row.get("ip.proto")),

                "tcp.srcport": clean(row.get("tcp.srcport")),
                "tcp.dstport": clean(row.get("tcp.dstport")),
                "tcp.flags": clean(row.get("tcp.flags")),

                "udp.srcport": clean(row.get("udp.srcport")),
                "udp.dstport": clean(row.get("udp.dstport")),

                "ntp.stratum": clean(row.get("ntp.stratum")),
                "ntp.ppoll": clean(row.get("ntp.ppoll")),
                "ntp.precision": clean(row.get("ntp.precision")),
                "ntp.rootdelay": clean(row.get("ntp.rootdelay")),
                "ntp.rootdispersion": clean(row.get("ntp.rootdispersion")),
                "ntp.refid": clean(row.get("ntp.refid")),
                "ntp.org": clean(row.get("ntp.org")),
                "ntp.rec": clean(row.get("ntp.rec")),
                "ntp.xmt": clean(row.get("ntp.xmt")),
                "protocol.anomaly": anomaly,
            }

            output.append(packet)

    with open(OUTPUT_JSON, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Done. Wrote {len(output)} packets → {OUTPUT_JSON}")


if __name__ == "__main__":
    main()