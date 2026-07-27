from cti.virustotal import check_virustotal
from cti.abuseipdb import check_abuseip


def get_threat_intelligence(ip):

    vt = check_virustotal(ip)

    abuse = check_abuseip(ip)

    return {
        "ip": ip,
        "virustotal": vt,
        "abuseipdb": abuse
    }


if __name__ == "__main__":

    ip = input("Enter IP Address: ")

    result = get_threat_intelligence(ip)

    print(result)