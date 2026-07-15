import dns.resolver

from garlicsmtp.transport.dns.exceptions import DNSLookupError
from garlicsmtp.transport.dns.records import MXRecord


class DNSResolver:

    def lookup_mx(self, domain: str) -> list[MXRecord]:
        try:
            answers = dns.resolver.resolve(
                domain,
                "MX",
            )

            records = [
                MXRecord(
                    priority=answer.preference,
                    exchange=str(answer.exchange).rstrip("."),
                )
                for answer in answers
            ]

            return sorted(
                records,
                key=lambda record: record.priority,
            )

        except Exception as exc:
            raise DNSLookupError(
                f"MX lookup failed for {domain}: {exc}"
            ) from exc