import re
from urllib.parse import urlparse
from typing import Dict, Optional
import tldextract
import dns.resolver
import socket
from app.exceptions import FeatureExtractionError
from app.logger import setup_logger

logger = setup_logger(__name__)

class FeatureExtractor:
    def __init__(self):
        self.suspicious_words = [
            'PayPal', 'login', 'signin', 'bank', 'account', 'update', 'free', 
            'lucky', 'service', 'bonus', 'ebayisapi', 'webscr', 'secure', 
            'banking', 'confirm', 'verify', 'authentication', 'wallet'
        ]
        self.shortening_services = [
            'bit.ly', 'goo.gl', 'shorte.st', 'go2l.ink', 'x.co', 'ow.ly', 
            't.co', 'tinyurl', 'tr.im', 'is.gd', 'cli.gs', 'yfrog.com', 
            'migre.me', 'ff.im', 'tiny.cc', 'url4.eu', 'twit.ac', 'su.pr', 
            'twurl.nl', 'snipurl.com', 'short.to', 'BudURL.com', 'ping.fm', 
            'post.ly', 'Just.as', 'bkite.com', 'snipr.com', 'fic.kr', 'loopt.us',
            'doiop.com', 'short.ie', 'kl.am', 'wp.me', 'rubyurl.com'
        ]

    def extract_features(self, url: str, label: Optional[int] = None) -> Dict:
        try:
            parsed_url = urlparse(url)
            extracted = tldextract.extract(url)
            domain = parsed_url.netloc

            # Combine all features
            features = {
                # Lexical features
                **self._get_lexical_features(url, parsed_url),
                # Host-based features
                **self._get_host_features(domain, parsed_url, extracted),
                # Security features
                **self._get_security_features(url, domain),
                # Domain features
                **self._get_domain_features(extracted, domain),
                # DNS features
                **self._get_dns_features(domain)
            }

            if label is not None:
                features["result"] = label

            return features

        except Exception as e:
            logger.error(f"Error in feature extraction: {e}")
            raise FeatureExtractionError(f"Error in feature extraction: {e}")

    def _get_lexical_features(self, url: str, parsed_url) -> Dict:
        return {
            "use_of_ip": self._having_ip_address(url),
            "abnormal_url": self._abnormal_url(url),
            "count.": url.count('.'),
            "count-www": url.lower().count('www'),
            "count@": url.count('@'),
            "count_dir": self._no_of_dir(url),
            "count_embed_domain": self._no_of_embed(url),
            "sus_url": self._suspicious_words(url),
            "short_url": self._shortening_service(url),
            "count_https": url.lower().count('https'),
            "count_http": url.lower().count('http'),
            "count%": url.count('%'),
            "count?": url.count('?'),
            "count-": url.count('-'),
            "count=": url.count('='),
            "url_length": len(url),
            "hostname_length": self._hostname_length(url),
            "fd_length": self._fd_length(url),
            "tld": self._get_tld(parsed_url.netloc),
            "tld_length": self._tld_length(url),
            "count_digits": sum(c.isdigit() for c in url),
            "count_letters": sum(c.isalpha() for c in url)
        }

    def _get_host_features(self, domain: str, parsed_url, extracted) -> Dict:
        features = {
            "has_valid_dns": self._check_dns_record(domain),
            "has_dns_record": self._has_dns_record(domain),
            "domain_length": len(domain),
            "has_https": 1 if parsed_url.scheme == 'https' else 0,
            "domain_in_path": 1 if domain.lower() in parsed_url.path.lower() else 0,
            "path_length": len(parsed_url.path),
            "qty_params": len(parsed_url.query.split('&')) if parsed_url.query else 0,
            "qty_fragments": len(parsed_url.fragment.split('#')) if parsed_url.fragment else 0,
            "qty_special_chars": len(re.findall(r'[^a-zA-Z0-9\s]', parsed_url.path)),
            "param_length": len(parsed_url.query),
            "fragment_length": len(parsed_url.fragment),
            "domain_token_count": len(re.findall(r'\w+', domain))
        }
        return features

    def _get_security_features(self, url: str, domain: str) -> Dict:
        return {
            "qty_sensitive_words": sum(1 for word in self.suspicious_words if word.lower() in url.lower()),
            "has_client": 1 if 'client' in url.lower() else 0,
            "has_admin": 1 if 'admin' in url.lower() else 0,
            "has_server": 1 if 'server' in url.lower() else 0,
            "has_login": 1 if 'login' in url.lower() else 0,
            "has_signup": 1 if any(x in url.lower() for x in ['signup', 'register', 'join']) else 0,
            "has_password": 1 if 'password' in url.lower() else 0,
            "has_security": 1 if 'security' in url.lower() else 0,
            "has_verify": 1 if 'verify' in url.lower() else 0,
            "has_auth": 1 if 'auth' in url.lower() else 0
        }

    def _get_domain_features(self, extracted, domain: str) -> Dict:
        return {
            "subdomain_length": len(extracted.subdomain),
            "qty_subdomains": len(extracted.subdomain.split('.')) if extracted.subdomain else 0,
            "domain_hyphens": extracted.domain.count('-'),
            "domain_underscores": extracted.domain.count('_'),
            "domain_digits": sum(c.isdigit() for c in domain),
            "has_port": 1 if re.search(r':[0-9]+', domain) else 0,
            "is_ip": 1 if self._is_ip(domain) else 0,
            "domain_length": len(extracted.domain)
        }

    def _get_dns_features(self, domain: str) -> Dict:
        features = {
            "qty_mx_records": 0,
            "qty_txt_records": 0,
            "qty_ns_records": 0
        }
        
        try:
            features["qty_mx_records"] = len(list(dns.resolver.resolve(domain, 'MX')))
        except:
            pass
            
        try:
            features["qty_txt_records"] = len(list(dns.resolver.resolve(domain, 'TXT')))
        except:
            pass
            
        try:
            features["qty_ns_records"] = len(list(dns.resolver.resolve(domain, 'NS')))
        except:
            pass
            
        return features

    # Helper methods
    def _having_ip_address(self, url: str) -> int:
        ip_pattern = r'(([01]?\d\d?|2[0-4]\d|25[0-5])\.){3}([01]?\d\d?|2[0-4]\d|25[0-5])'
        return 1 if re.search(ip_pattern, url) else 0

    def _abnormal_url(self, url: str) -> int:
        hostname = urlparse(url).hostname
        return 1 if hostname and hostname not in url else 0

    def _no_of_dir(self, url: str) -> int:
        return urlparse(url).path.count('/')

    def _no_of_embed(self, url: str) -> int:
        return url.count('//') - 1

    def _shortening_service(self, url: str) -> int:
        return 1 if any(service in url for service in self.shortening_services) else 0

    def _hostname_length(self, url: str) -> int:
        return len(urlparse(url).netloc)

    def _suspicious_words(self, url: str) -> int:
        return 1 if any(word in url.lower() for word in self.suspicious_words) else 0

    def _fd_length(self, url: str) -> int:
        urlpath = urlparse(url).path
        try:
            return len(urlpath.split('/')[1])
        except:
            return 0

    def _tld_length(self, url: str) -> int:
        try:
            return len(urlparse(url).netloc.split('.')[-1])
        except:
            return 0

    def _get_tld(self, domain: str) -> str:
        try:
            return domain.split('.')[-1]
        except:
            return ""

    def _check_dns_record(self, domain: str) -> int:
        try:
            dns.resolver.resolve(domain, 'A')
            return 1
        except:
            return 0

    def _has_dns_record(self, domain: str) -> int:
        try:
            socket.gethostbyname(domain)
            return 1
        except:
            return 0

    def _is_ip(self, domain: str) -> bool:
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        return bool(re.match(ip_pattern, domain))