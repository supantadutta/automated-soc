"""20 realistic SOC sample alerts (safe fake IOCs only)."""
from __future__ import annotations

SAMPLE_ALERTS: list[dict] = [
    {
        "title": "Suspicious Active Directory Authentication Activity", "source_tool": "CrowdStrike",
        "severity": "High", "customer": "Globex",
        "raw": '{"DetectName":"Suspicious AD Authentication","source_tool":"CrowdStrike","severity":"High","UserName":"svc-backup","ComputerName":"DC01","RemoteIP":"192.168.143.84","timestamp":"2026-06-14T22:14:03Z","detail":"Multiple authentication attempts against Active Directory involving multiple usernames"}',
    },
    {
        "title": "Password Spray Detected Against Microsoft 365", "source_tool": "Microsoft Sentinel",
        "severity": "High", "customer": "Globex",
        "raw": '{"alert_name":"Password Spray","source_tool":"Sentinel","severity":"High","src_ip":"203.0.113.45","timestamp":"2026-06-14T09:02:10Z","distinct_users":37,"detail":"Single source attempted logins across 37 accounts with common passwords"}',
    },
    {
        "title": "Successful Brute Force After Repeated Failures", "source_tool": "Splunk",
        "severity": "Critical", "customer": "Initech",
        "raw": '{"search_name":"Brute Force Success","source_tool":"Splunk","severity":"Critical","user":"jdoe","src":"198.51.100.23","dest":"10.20.5.7","failed":214,"succeeded":1,"detail":"214 failed authentications followed by one success"}',
    },
    {
        "title": "Unusual Login - Impossible Travel", "source_tool": "Microsoft Sentinel",
        "severity": "Medium", "customer": "Globex",
        "raw": '{"alert_name":"Impossible Travel","source_tool":"Sentinel","severity":"Medium","user":"awhite","src_ip":"203.0.113.77","geo":"Singapore then Brazil in 20m","timestamp":"2026-06-14T11:45:00Z"}',
    },
    {
        "title": "New Endpoint First-Seen for Privileged Account", "source_tool": "CrowdStrike",
        "severity": "Medium", "customer": "Initech",
        "raw": '{"DetectName":"New Endpoint Usage","source_tool":"CrowdStrike","severity":"Medium","UserName":"admin-ops","ComputerName":"WKS-NEW-22","RemoteIP":"10.20.9.40","detail":"First-seen host for a privileged account"}',
    },
    {
        "title": "RDP Login Anomaly from External IP", "source_tool": "Wazuh",
        "severity": "High", "customer": "Initech",
        "raw": '{"rule":{"description":"RDP Login Anomaly","level":10},"data":{"srcip":"203.0.113.66","dstuser":"contractor1"},"source_tool":"Wazuh","detail":"RDP (3389) login from external IP outside business hours"}',
    },
    {
        "title": "SSH Brute Force Against Bastion Host", "source_tool": "Wazuh",
        "severity": "High", "customer": "Initech",
        "raw": '{"rule":{"description":"SSH Brute Force","level":10},"data":{"srcip":"198.51.100.91","dstuser":"root"},"source_tool":"Wazuh","detail":"sshd: 480 failed password attempts for root in 5 minutes"}',
    },
    {
        "title": "Suspicious PowerShell Execution", "source_tool": "CrowdStrike",
        "severity": "High", "customer": "Globex",
        "raw": '{"DetectName":"Suspicious PowerShell","source_tool":"CrowdStrike","severity":"High","UserName":"mlee","ComputerName":"FIN-WKS-08","CommandLine":"powershell.exe -nop -w hidden -enc SQBFAFgA","detail":"Hidden window PowerShell with execution"}',
    },
    {
        "title": "Encoded Command Line Detected", "source_tool": "Elastic",
        "severity": "High", "customer": "Globex",
        "raw": '{"source":{"ip":"10.10.4.5"},"user":{"name":"mlee"},"host":{"name":"FIN-WKS-08"},"process":{"command_line":"cmd.exe /c powershell -enc aQBlAHgA"},"source_tool":"Elastic","severity":"High","alert_name":"Encoded Command"}',
    },
    {
        "title": "Credential Dumping Behaviour (LSASS Access)", "source_tool": "CrowdStrike",
        "severity": "Critical", "customer": "Initech",
        "raw": '{"DetectName":"Credential Dumping","source_tool":"CrowdStrike","severity":"Critical","UserName":"SYSTEM","ComputerName":"HR-SRV-02","process":"rundll32.exe","detail":"Suspicious access to lsass.exe memory consistent with credential theft"}',
    },
    {
        "title": "Possible DLL Injection into Explorer", "source_tool": "CrowdStrike",
        "severity": "High", "customer": "Globex",
        "raw": '{"DetectName":"Process Injection","source_tool":"CrowdStrike","severity":"High","ComputerName":"ENG-WKS-14","process":"explorer.exe","detail":"Reflective DLL injection suspected into explorer.exe"}',
    },
    {
        "title": "Malware Hash Detected on Endpoint", "source_tool": "CrowdStrike",
        "severity": "Critical", "customer": "Initech",
        "raw": '{"DetectName":"Malicious File","source_tool":"CrowdStrike","severity":"Critical","ComputerName":"SALES-WKS-03","FileName":"invoice.exe","sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","detail":"Known malicious file quarantined"}',
    },
    {
        "title": "Directory Traversal Attempt on Web Portal", "source_tool": "F5",
        "severity": "Medium", "customer": "Globex",
        "raw": '{"source_tool":"F5","severity":"Medium","src_ip":"203.0.113.120","url":"https://portal.globex.test/../../etc/passwd","detail":"Path traversal pattern ../../ detected in request URI"}',
    },
    {
        "title": "SQL Injection Attempt Blocked by WAF", "source_tool": "F5",
        "severity": "High", "customer": "Globex",
        "raw": '{"source_tool":"F5 ASM","severity":"High","src_ip":"203.0.113.150","url":"https://shop.globex.test/item?id=1\' OR \'1\'=\'1","detail":"WAF blocked SQL injection signature union select"}',
    },
    {
        "title": "Reflected XSS Attempt Detected", "source_tool": "F5",
        "severity": "Medium", "customer": "Globex",
        "raw": '{"source_tool":"F5 ASM","severity":"Medium","src_ip":"203.0.113.151","url":"https://shop.globex.test/search?q=<script>alert(1)</script>","detail":"Cross-site scripting payload detected"}',
    },
    {
        "title": "WAF Blocked Web Application Attack Burst", "source_tool": "F5",
        "severity": "Medium", "customer": "Initech",
        "raw": '{"source_tool":"F5 ASM","severity":"Medium","src_ip":"198.51.100.200","detail":"Web application firewall blocked 132 malicious requests in 2 minutes"}',
    },
    {
        "title": "Suspicious DNS Query to Low-Reputation Domain", "source_tool": "Elastic",
        "severity": "Medium", "customer": "Initech",
        "raw": '{"source":{"ip":"10.20.6.30"},"host":{"name":"MKT-WKS-09"},"domain":"malicious-domain.test","source_tool":"Elastic","severity":"Medium","alert_name":"Suspicious DNS Query"}',
    },
    {
        "title": "DNS Tunneling Suspicion (High Entropy Subdomains)", "source_tool": "Suricata",
        "severity": "High", "customer": "Globex",
        "raw": '{"alert":{"signature":"DNS Tunneling Suspected","severity":1},"src_ip":"10.10.7.21","dest_ip":"203.0.113.88","domain":"x7f3a9q2.evil-c2.example","source_tool":"Suricata","detail":"High entropy DNS subdomains indicative of tunneling"}',
    },
    {
        "title": "C2 Domain Communication Detected", "source_tool": "Suricata",
        "severity": "Critical", "customer": "Initech",
        "raw": '{"alert":{"signature":"C2 Beacon to Known Bad Domain","severity":1},"src_ip":"10.20.8.55","dest_ip":"203.0.113.66","domain":"beacon.evil-c2.example","source_tool":"Suricata","detail":"Periodic beaconing to known command-and-control domain"}',
    },
    {
        "title": "Lateral Movement via SMB (Admin Share Access)", "source_tool": "Elastic",
        "severity": "High", "customer": "Initech",
        "raw": '{"source":{"ip":"10.20.5.7"},"user":{"name":"admin-ops"},"host":{"name":"HR-SRV-02"},"source_tool":"Elastic","severity":"High","alert_name":"Lateral Movement via SMB","detail":"Access to ADMIN$ share from another internal host using PsExec-like behaviour"}',
    },
]
