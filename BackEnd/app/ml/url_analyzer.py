import requests
import socket
import dns.resolver
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import whois
from datetime import datetime
import concurrent.futures
from app.logger import setup_logger
import ipaddress
import tldextract

logger = setup_logger(__name__)

class URLAnalyzer:
    def __init__(self):
        self.ip_api_endpoint = "http://ip-api.com/batch?fields=32698367"

    def _get_ip_info(self, domain: str) -> Dict[str, Any]:
        """Get IP and location information using batch IP API."""
        try:
            # Get IP address
            ip = socket.gethostbyname(domain)
            
            # Prepare payload for IP API
            payload = [{
                "query": ip,
                "fields": "status,country,countryCode,region,regionName,city,zip,lat,lon,timezone,currency,isp,org,as,asname,proxy,hosting",
                "lang": "en"
            }]

            response = requests.post(self.ip_api_endpoint, json=payload)
            if response.status_code == 200:
                data = response.json()[0]  # Get first result since we're only querying one IP
                if data.get("status") == "success":
                    return {
                        "hosting_details": {
                            "country": data.get("country", "Unknown"),
                            "city": data.get("city", "Unknown"),
                            "region": data.get("regionName", "Unknown"),
                            "provider": data.get("org", "Unknown"),
                            "is_hosting_provider": data.get("hosting", False),
                            "is_proxy": data.get("proxy", False),
                            "org": data.get("org", "Unknown"),
                            "latitude": data.get("lat"),
                            "longitude": data.get("lon"),
                            "timezone": data.get("timezone")
                        },
                        "network_info": {
                            "isp": data.get("isp", "Unknown"),
                            "organization": data.get("asname", "Unknown")
                        }
                    }
        except Exception as e:
            logger.error(f"Error getting IP info: {e}")
        
        return self._get_default_ip_info()

    def _get_default_ip_info(self) -> Dict[str, Any]:
        """Return default IP info structure."""
        return {
            "hosting_details": {
                "country": "Unknown",
                "city": "Unknown",
                "region": "Unknown",
                "provider": "Unknown",
                "is_hosting_provider": False,
                "is_proxy": False
            },
            "network_info": {
                "isp": "Unknown",
                "organization": "Unknown"
            }
        }

    def _get_dns_info(self, domain: str) -> Dict[str, bool]:
        """Get simplified DNS information."""
        dns_info = {
            "has_valid_dns": False,
            "has_mail_server": False,
            "has_security_records": False
        }

        try:
            # Check basic DNS
            try:
                dns.resolver.resolve(domain, 'A')
                dns_info["has_valid_dns"] = True
            except:
                pass

            # Check mail server
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                dns_info["has_mail_server"] = len(list(mx_records)) > 0
            except:
                pass

            # Check security records (SPF or DMARC)
            try:
                txt_records = dns.resolver.resolve(domain, 'TXT')
                records = [str(record) for record in txt_records]
                dns_info["has_security_records"] = any("v=spf1" in r or "v=DMARC1" in r for r in records)
            except:
                pass

        except Exception as e:
            logger.error(f"Error getting DNS info: {e}")

        return dns_info

    def _check_security_headers(self, url: str) -> Dict[str, bool]:
        """Check security headers of the website."""
        security_headers = {
            "Strict-Transport-Security": False,
            "X-Content-Type-Options": False,
            "X-Frame-Options": False,
            "X-XSS-Protection": False,
            "Content-Security-Policy": False
        }

        try:
            response = requests.head(
                url if url.startswith('http') else f'https://{url}',
                timeout=5,
                allow_redirects=True
            )
            headers = response.headers

            security_headers["Strict-Transport-Security"] = "strict-transport-security" in headers.keys()
            security_headers["X-Content-Type-Options"] = "x-content-type-options" in headers.keys()
            security_headers["X-Frame-Options"] = "x-frame-options" in headers.keys()
            security_headers["X-XSS-Protection"] = "x-xss-protection" in headers.keys()
            security_headers["Content-Security-Policy"] = "content-security-policy" in headers.keys()

        except Exception as e:
            logger.error(f"Error checking security headers: {e}")

        return security_headers

    def analyze_url(self, url: str, prediction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze URL and provide user-friendly explanation with additional details."""
        # Remove async/await since we're using ThreadPoolExecutor for concurrency
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc

            # Gather information concurrently
            with concurrent.futures.ThreadPoolExecutor() as executor:
                ip_info_future = executor.submit(self._get_ip_info, domain)
                dns_info_future = executor.submit(self._get_dns_info, domain)

                ip_info = ip_info_future.result()
                dns_info = dns_info_future.result()

            # Rest of the code remains the same...
            hosting_info = ip_info["hosting_details"]
            trust_indicators = []
            concerns = []

            # Add trust indicators based on analysis
            if dns_info["has_valid_dns"]:
                trust_indicators.append("Valid website registration")
            if dns_info["has_mail_server"]:
                trust_indicators.append("Professional email setup")
            if dns_info["has_security_records"]:
                trust_indicators.append("Enhanced email security")
            if not hosting_info["is_proxy"]:
                trust_indicators.append("Direct connection (no proxy)")

            # Add concerns based on analysis
            if hosting_info["is_proxy"]:
                concerns.append("Connection through proxy detected")
            if not dns_info["has_valid_dns"]:
                concerns.append("Website might be newly registered or temporary")
            if prediction_result.get("is_malicious"):
                concerns.append("Suspicious URL patterns detected")

            return {
                "website_details": {
                    "hosting_location": {
                        "display": f"{hosting_info['city']}, {hosting_info['country']}",
                        "country": hosting_info['country'],
                        "city": hosting_info['city'],
                        "region": hosting_info['region'],
                        "coordinates": {
                            "latitude": hosting_info.get('latitude'),
                            "longitude": hosting_info.get('longitude')
                        }
                    },
                    "organization": {
                        "name": hosting_info['provider'],
                        "org_details": hosting_info.get('org', 'Unknown'),
                        "isp": ip_info['network_info']['isp'],
                        "type": "Business/Organization Website" if dns_info["has_mail_server"] else "Basic Website"
                    },
                    "security_features": {
                        "email_security": "Present" if dns_info["has_security_records"] else "Not Found",
                        "professional_setup": dns_info["has_mail_server"],
                        "direct_connection": not hosting_info["is_proxy"]
                    }
                },
                "trust_analysis": {
                    "trust_indicators": trust_indicators,
                    "concerns": concerns,
                    "recommendation": self._get_recommendation(
                        prediction_result.get("is_malicious", False),
                        len(concerns),
                        len(trust_indicators)
                    )
                },
                "technical_details": {
                    "network": {
                        "organization": hosting_info.get('org', 'Unknown'),
                        "isp_details": ip_info['network_info']['isp'],
                        "is_hosting_provider": hosting_info['is_hosting_provider'],
                        "is_proxy": hosting_info['is_proxy']
                    },
                    "location": {
                        "latitude": hosting_info.get('latitude'),
                        "longitude": hosting_info.get('longitude'),
                        "timezone": hosting_info.get('timezone', 'Unknown')
                    },
                    "dns_configuration": {
                        "has_valid_dns": dns_info["has_valid_dns"],
                        "has_mail_server": dns_info["has_mail_server"],
                        "has_security_records": dns_info["has_security_records"]
                    }
                }
            }

        except Exception as e:
            logger.error(f"Error in URL analysis: {e}")
            return self._get_default_analysis(url, prediction_result)
        
    def _get_recommendation(self, is_malicious: bool, num_concerns: int, num_trust_indicators: int) -> str:
        """Get user-friendly recommendation."""
        if is_malicious:
            return "This website shows significant risk factors. We recommend avoiding it."
        elif num_concerns > num_trust_indicators:
            return "Exercise caution when visiting this website. Consider verifying its legitimacy."
        elif num_concerns > 0:
            return "The website appears generally safe but has some minor concerns."
        else:
            return "This appears to be a legitimate website with good security practices."

    def _calculate_security_score(self, security_headers: Dict[str, bool], dns_info: Dict[str, Any]) -> int:
        """Calculate security score out of 100."""
        score = 0
        
        # Security headers scoring (50 points max)
        header_weights = {
            "Strict-Transport-Security": 15,
            "Content-Security-Policy": 15,
            "X-Frame-Options": 7,
            "X-XSS-Protection": 7,
            "X-Content-Type-Options": 6
        }
        
        for header, weight in header_weights.items():
            if security_headers.get(header, False):
                score += weight

        # DNS configuration scoring (50 points max)
        if any("v=spf1" in record for record in dns_info["txt_records"]):
            score += 15
        if any("v=DMARC1" in record for record in dns_info["txt_records"]):
            score += 15
        if len(dns_info["mx_records"]) > 0:
            score += 10
        if len(dns_info["ns_records"]) >= 2:
            score += 10

        return score

    def _calculate_infrastructure_score(self, ip_info: Dict[str, Any], dns_info: Dict[str, Any]) -> int:
        """Calculate infrastructure score out of 100."""
        score = 0

        # Network infrastructure (50 points)
        if ip_info["network"]["asname"] != "Unknown":
            score += 20
        if ip_info["network"]["isp"] != "Unknown":
            score += 15
        if ip_info["location"]["country"] != "Unknown":
            score += 15

        # DNS infrastructure (50 points)
        if len(dns_info["mx_records"]) > 0:
            score += 15
        if len(dns_info["ns_records"]) >= 2:
            score += 15
        if len(dns_info["txt_records"]) > 0:
            score += 10
        if dns_info["has_dns"]:
            score += 10

        return score

    def _get_security_concerns(self, security_headers: Dict[str, bool], dns_info: Dict[str, Any]) -> List[Dict[str, str]]:
        """Get list of security concerns."""
        concerns = []
        
        # Check security headers
        for header, present in security_headers.items():
            if not present:
                concerns.append({
                    "type": "Security Header Missing",
                    "description": f"Missing {header} security header",
                    "severity": "High" if header in ["Strict-Transport-Security", "Content-Security-Policy"] else "Medium"
                })

        # Check DNS configuration
        if not any("v=spf1" in record for record in dns_info["txt_records"]):
            concerns.append({
                "type": "DNS Configuration",
                "description": "Missing SPF record for email security",
                "severity": "Medium"
            })

        if not any("v=DMARC1" in record for record in dns_info["txt_records"]):
            concerns.append({
                "type": "DNS Configuration",
                "description": "Missing DMARC record for email security",
                "severity": "Medium"
            })

        return concerns

    def _get_trust_factors(self, ip_info: Dict[str, Any], dns_info: Dict[str, Any]) -> List[Dict[str, str]]:
        """Get list of trust factors."""
        factors = []

        # Network factors
        if ip_info["network"]["asname"] != "Unknown":
            factors.append({
                "type": "Infrastructure",
                "description": f"Hosted by known provider: {ip_info['network']['asname']}",
                "impact": "Positive"
            })

        # DNS factors
        if len(dns_info["mx_records"]) > 0:
            factors.append({
                "type": "Email Configuration",
                "description": "Professional email setup with MX records",
                "impact": "Positive"
            })

        if len(dns_info["ns_records"]) >= 2:
            factors.append({
                "type": "DNS Configuration",
                "description": "Redundant DNS setup with multiple nameservers",
                "impact": "Positive"
            })

        return factors

    def _is_ip_address(self, domain: str) -> bool:
        """Check if domain is an IP address."""
        try:
            ipaddress.ip_address(domain)
            return True
        except ValueError:
            return False

    def _get_default_analysis(self, url: str, prediction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Return default analysis structure."""
        return {
            "prediction": {
                "result": prediction_result.get("result", "Unknown"),
                "confidence": prediction_result.get("confidence", 0.0),
                "is_malicious": prediction_result.get("is_malicious", False)
            },
            "website_details": {
                "hosting_location": {
                    "display": "Unknown",
                    "country": "Unknown",
                    "city": "Unknown",
                    "region": "Unknown",
                    "coordinates": {
                        "latitude": None,
                        "longitude": None
                    }
                },
                "organization": {
                    "name": "Unknown",
                    "org_details": "Unknown",
                    "isp": "Unknown",
                    "type": "Unknown"
                },
                "security_features": {
                    "email_security": "Unknown",
                    "professional_setup": False,
                    "direct_connection": True
                }
            },
            "trust_analysis": {
                "trust_indicators": [],
                "concerns": ["Unable to perform complete analysis"],
                "recommendation": "Unable to provide detailed analysis. Exercise caution."
            },
            "technical_details": {
                "network": {
                    "organization": "Unknown",
                    "isp_details": "Unknown",
                    "is_hosting_provider": False,
                    "is_proxy": False
                },
                "location": {
                    "latitude": None,
                    "longitude": None,
                    "timezone": "Unknown"
                },
                "dns_configuration": {
                    "has_valid_dns": False,
                    "has_mail_server": False,
                    "has_security_records": False
                }
            }
        }
