"""Registered node address book query backed by mirror REST APIs."""

from __future__ import annotations

import ipaddress
from urllib.parse import ParseResult, urlencode, urljoin, urlparse, urlunparse

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import (
    BlockNodeServiceEndpoint,
)
from hiero_sdk_python.address_book.general_service_endpoint import (
    GeneralServiceEndpoint,
)
from hiero_sdk_python.address_book.mirror_node_service_endpoint import (
    MirrorNodeServiceEndpoint,
)
from hiero_sdk_python.address_book.registered_node import RegisteredNode
from hiero_sdk_python.address_book.registered_node_address_book import (
    RegisteredNodeAddressBook,
)
from hiero_sdk_python.address_book.registered_service_endpoint import (
    RegisteredServiceEndpoint,
)
from hiero_sdk_python.address_book.rpc_relay_service_endpoint import (
    RpcRelayServiceEndpoint,
)
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.utils.entity_id_helper import perform_query_to_mirror_node


class RegisteredNodeAddressBookQuery:
    """Query registered nodes from mirror REST APIs."""

    _REGISTERED_NODES_PATH = "/network/registered-nodes"
    _VALID_ORDER = {"asc", "desc"}
    _VALID_NODE_TYPES = {
        "BLOCK_NODE",
        "GENERAL_SERVICE",
        "MIRROR_NODE",
        "RPC_RELAY",
    }
    _VALID_ID_OPERATORS = {"eq", "gt", "gte", "lt", "lte"}

    def __init__(self) -> None:
        self._limit: int | None = None
        self._order: str = "asc"
        self._node_type: str | None = None
        self._registered_node_id_filters: list[str] = []

    def set_limit(self, limit: int | None) -> RegisteredNodeAddressBookQuery:
        """Set the number of registered nodes to request per mirror page."""
        if limit is not None and limit <= 0:
            raise ValueError("limit must be a positive integer.")

        self._limit = limit
        return self

    def set_order(self, order: str) -> RegisteredNodeAddressBookQuery:
        """Set the sort order for registered node IDs (asc or desc)."""
        normalized_order = order.lower().strip()
        if normalized_order not in self._VALID_ORDER:
            raise ValueError("order must be one of: asc, desc.")

        self._order = normalized_order
        return self

    def set_type(self, node_type: str | None) -> RegisteredNodeAddressBookQuery:
        """Set an optional registered node type filter."""
        if node_type is None:
            self._node_type = None
            return self

        normalized_type = node_type.upper().strip()
        if normalized_type not in self._VALID_NODE_TYPES:
            raise ValueError("type must be one of: BLOCK_NODE, GENERAL_SERVICE, MIRROR_NODE, RPC_RELAY.")

        self._node_type = normalized_type
        return self

    def set_registered_node_id(self, registered_node_id: int) -> RegisteredNodeAddressBookQuery:
        """Set an equality filter for registered node ID."""
        if registered_node_id < 0:
            raise ValueError("registered_node_id must be non-negative.")

        self._registered_node_id_filters = [f"eq:{registered_node_id}"]
        return self

    def add_registered_node_id_filter(self, operator: str, value: int) -> RegisteredNodeAddressBookQuery:
        """Add a range filter using registerednode.id query operators."""
        normalized_operator = operator.lower().strip()
        if normalized_operator not in self._VALID_ID_OPERATORS:
            raise ValueError("operator must be one of: eq, gt, gte, lt, lte.")
        if value < 0:
            raise ValueError("registered node id filter value must be non-negative.")

        if normalized_operator == "eq" and self._registered_node_id_filters:
            raise ValueError("eq filter cannot be combined with other registered node id filters.")

        if normalized_operator != "eq" and any(f.startswith("eq:") for f in self._registered_node_id_filters):
            raise ValueError("Cannot add range filters when an eq filter is already set.")

        self._registered_node_id_filters.append(f"{normalized_operator}:{value}")
        return self

    def execute(self, client: Client, timeout: int | float | None = None) -> RegisteredNodeAddressBook:
        """Execute the query using the configured mirror node REST API."""
        base_url = self._normalize_mirror_rest_url(client.network.get_mirror_rest_url()).rstrip("/")
        request_timeout = 10.0 if timeout is None else float(timeout)

        next_url = self._build_initial_url(base_url)
        registered_nodes: list[RegisteredNode] = []

        while next_url:
            response = perform_query_to_mirror_node(next_url, timeout=request_timeout)
            page_nodes, next_link = self._parse_response_page(response, base_url)
            registered_nodes.extend(page_nodes)
            next_url = next_link

        return RegisteredNodeAddressBook.from_iterable(registered_nodes)

    def _normalize_mirror_rest_url(self, base_url: str) -> str:
        """Use the REST port for local mirror registered-node APIs."""
        parsed_url = urlparse(base_url)
        if parsed_url.hostname not in {"localhost", "127.0.0.1"} or parsed_url.port != 5551:
            return base_url

        netloc = self._replace_port(parsed_url, 8084)
        return urlunparse(parsed_url._replace(netloc=netloc))

    def _replace_port(self, parsed_url: ParseResult, port: int) -> str:
        """Return a netloc with the supplied port and existing user info."""
        host = parsed_url.hostname or ""
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"

        user_info = ""
        if parsed_url.username is not None:
            user_info = parsed_url.username
            if parsed_url.password is not None:
                user_info = f"{user_info}:{parsed_url.password}"
            user_info = f"{user_info}@"

        return f"{user_info}{host}:{port}"

    def _build_initial_url(self, base_url: str) -> str:
        """Build the first request URL based on current query settings."""
        params: list[tuple[str, str]] = []

        if self._is_local_registered_nodes_endpoint(base_url):
            params.extend(("registerednode.id", value) for value in self._registered_node_id_filters)
            query = urlencode(params, doseq=True)
            if not query:
                return f"{base_url}{self._REGISTERED_NODES_PATH}"
            return f"{base_url}{self._REGISTERED_NODES_PATH}?{query}"

        params.append(("order", self._order))

        if self._limit is not None:
            params.append(("limit", str(self._limit)))

        if self._node_type is not None:
            params.append(("type", self._node_type))

        params.extend(("registerednode.id", value) for value in self._registered_node_id_filters)

        query = urlencode(params, doseq=True)
        if not query:
            return f"{base_url}{self._REGISTERED_NODES_PATH}"

        return f"{base_url}{self._REGISTERED_NODES_PATH}?{query}"

    def _is_local_registered_nodes_endpoint(self, base_url: str) -> bool:
        """Return True when querying a local mirror endpoint."""
        parsed_url = urlparse(base_url)
        return parsed_url.hostname in {"localhost", "127.0.0.1"} and parsed_url.port == 8084

    def _parse_response_page(self, response: dict, base_url: str) -> tuple[list[RegisteredNode], str | None]:
        """Parse a mirror response page and return models plus the next URL."""
        raw_nodes = response.get("registered_nodes")
        if not isinstance(raw_nodes, list):
            raise ValueError("Mirror response must include a 'registered_nodes' list.")

        parsed_nodes = [self._parse_registered_node(node) for node in raw_nodes]

        links = response.get("links")
        if not isinstance(links, dict):
            return parsed_nodes, None

        next_link = links.get("next")
        if not isinstance(next_link, str) or not next_link:
            return parsed_nodes, None

        if next_link.startswith("http://") or next_link.startswith("https://"):
            return parsed_nodes, next_link

        return parsed_nodes, urljoin(f"{base_url}/", next_link)

    def _parse_registered_node(self, raw_node: dict) -> RegisteredNode:
        """Parse a single registered node object from mirror JSON."""
        registered_node_id = raw_node.get("registered_node_id")
        if not isinstance(registered_node_id, int):
            raise ValueError("registered_node_id is required and must be an integer.")

        raw_endpoints = raw_node.get("service_endpoints", [])
        if not isinstance(raw_endpoints, list):
            raise ValueError("service_endpoints must be a list.")

        return RegisteredNode(
            registered_node_id=registered_node_id,
            admin_key=self._parse_admin_key(raw_node.get("admin_key")),
            description=self._optional_string(raw_node.get("description")),
            service_endpoints=tuple(self._parse_service_endpoint(endpoint) for endpoint in raw_endpoints),
        )

    def _parse_admin_key(self, raw_admin_key: dict | None) -> Key | None:
        """Parse mirror admin_key payload into an SDK Key when present."""
        if not isinstance(raw_admin_key, dict):
            return None

        key_hex = raw_admin_key.get("key")
        if not isinstance(key_hex, str) or not key_hex:
            return None

        key_type = str(raw_admin_key.get("_type", "")).strip().upper()

        if key_type == "ED25519":
            return PublicKey.from_string_ed25519(key_hex)

        if key_type in {"ECDSA_SECP256K1", "ECDSA"}:
            return PublicKey.from_string_ecdsa(key_hex)

        if key_type == "PROTOBUFENCODED":
            key_proto = basic_types_pb2.Key()
            key_proto.ParseFromString(bytes.fromhex(key_hex.removeprefix("0x")))
            return Key.from_proto_key(key_proto)

        return PublicKey.from_string(key_hex)

    def _parse_service_endpoint(self, raw_endpoint: dict) -> RegisteredServiceEndpoint:
        """Parse one registered service endpoint from mirror JSON."""
        common_kwargs = self._parse_endpoint_common_fields(raw_endpoint)
        endpoint_type = self._resolve_endpoint_type(raw_endpoint)

        if endpoint_type == "BLOCK_NODE":
            return BlockNodeServiceEndpoint(
                endpoint_apis=self._parse_block_node_apis(raw_endpoint.get("block_node")),
                **common_kwargs,
            )

        if endpoint_type == "MIRROR_NODE":
            return MirrorNodeServiceEndpoint(**common_kwargs)

        if endpoint_type == "RPC_RELAY":
            return RpcRelayServiceEndpoint(**common_kwargs)

        if endpoint_type == "GENERAL_SERVICE":
            general_service = raw_endpoint.get("general_service")
            description = None
            if isinstance(general_service, dict):
                description = self._optional_string(general_service.get("description"))
            return GeneralServiceEndpoint(description=description, **common_kwargs)

        raise ValueError(f"Unsupported endpoint type: {endpoint_type}")

    def _parse_endpoint_common_fields(self, raw_endpoint: dict) -> dict[str, object]:
        """Parse fields shared by all endpoint types."""
        ip_address = self._optional_string(raw_endpoint.get("ip_address"))
        domain_name = self._optional_string(raw_endpoint.get("domain_name"))
        requires_tls = bool(raw_endpoint.get("requires_tls", False))
        port = int(raw_endpoint.get("port", 0))

        packed_ip = None
        if ip_address is not None:
            packed_ip = ipaddress.ip_address(ip_address).packed

        return {
            "ip_address": packed_ip,
            "domain_name": domain_name,
            "port": port,
            "requires_tls": requires_tls,
        }

    def _resolve_endpoint_type(self, raw_endpoint: dict) -> str:
        """Resolve endpoint type from mirror payload fields."""
        explicit_type = self._optional_string(raw_endpoint.get("type"))
        if explicit_type is not None:
            normalized_type = explicit_type.upper()
            if normalized_type in self._VALID_NODE_TYPES:
                return normalized_type

        if raw_endpoint.get("block_node") is not None:
            return "BLOCK_NODE"
        if raw_endpoint.get("mirror_node") is not None:
            return "MIRROR_NODE"
        if raw_endpoint.get("rpc_relay") is not None:
            return "RPC_RELAY"
        if raw_endpoint.get("general_service") is not None:
            return "GENERAL_SERVICE"

        raise ValueError("Unable to determine registered service endpoint type.")

    def _parse_block_node_apis(self, raw_block_node: dict | None) -> list[BlockNodeApi]:
        """Parse the block node endpoint API list into SDK enum form."""
        if not isinstance(raw_block_node, dict):
            return [BlockNodeApi.OTHER]

        endpoint_apis = raw_block_node.get("endpoint_apis")
        if not isinstance(endpoint_apis, list) or not endpoint_apis:
            return [BlockNodeApi.OTHER]

        parsed_apis: list[BlockNodeApi] = []
        for endpoint_api in endpoint_apis:
            if not isinstance(endpoint_api, str):
                continue

            try:
                parsed_apis.append(BlockNodeApi[endpoint_api.upper().strip()])
            except KeyError:
                parsed_apis.append(BlockNodeApi.OTHER)

        return parsed_apis or [BlockNodeApi.OTHER]

    def _optional_string(self, value: object) -> str | None:
        """Return a normalized non-empty string or None."""
        if not isinstance(value, str):
            return None

        normalized = value.strip()
        return normalized or None
