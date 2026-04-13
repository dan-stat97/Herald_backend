import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class IVSProvisioningError(Exception):
    pass


@dataclass
class ProvisionedStream:
    provider: str
    playback_url: str
    ingest_endpoint: Optional[str]
    provider_stream_key: Optional[str]
    ivs_channel_arn: Optional[str]
    ivs_stage_arn: Optional[str]
    ivs_stage_rtmps_endpoint: Optional[str]
    ivs_stage_whip_endpoint: Optional[str]


@dataclass
class HostSession:
    token: str
    expires_at: Optional[datetime]
    participant_id: Optional[str]
    stage_arn: Optional[str]
    rtmps_endpoint: Optional[str]
    whip_endpoint: Optional[str]


def ivs_is_enabled() -> bool:
    return os.getenv('AWS_IVS_ENABLED', '').lower() in {'1', 'true', 'yes', 'on'}


def _require_boto3():
    try:
        import boto3  # type: ignore
    except ImportError as exc:
        raise IVSProvisioningError('boto3 is not installed for IVS provisioning.') from exc
    return boto3


def _region() -> str:
    region = os.getenv('AWS_IVS_REGION') or os.getenv('AWS_REGION')
    if not region:
        raise IVSProvisioningError('AWS_IVS_REGION or AWS_REGION is required for IVS provisioning.')
    return region


def _service_client(boto3_module, primary_name: str, fallback_name: Optional[str] = None):
    region = _region()
    try:
        return boto3_module.client(primary_name, region_name=region)
    except Exception:
        if not fallback_name:
            raise
        return boto3_module.client(fallback_name, region_name=region)


def provision_stream_resource(*, stream_id: str, title: str, record_enabled: bool = False) -> ProvisionedStream:
    if not ivs_is_enabled():
        raise IVSProvisioningError('AWS IVS provisioning is not enabled.')

    boto3 = _require_boto3()
    ivs = _service_client(boto3, 'ivs')
    ivs_realtime = _service_client(boto3, 'ivsrealtime', 'ivs-realtime')

    name = f"herald-{stream_id}"[:128]
    channel_params = {
        'name': name,
        'type': os.getenv('AWS_IVS_CHANNEL_TYPE', 'STANDARD'),
        'latencyMode': os.getenv('AWS_IVS_LATENCY_MODE', 'LOW'),
        'authorized': False,
        'tags': {
            'app': 'heraldsocial',
            'stream_id': stream_id,
            'title': title[:120],
        },
    }

    recording_arn = os.getenv('AWS_IVS_RECORDING_CONFIGURATION_ARN')
    if record_enabled and recording_arn:
        channel_params['recordingConfigurationArn'] = recording_arn

    channel_res = ivs.create_channel(**channel_params)
    channel = channel_res.get('channel', {})
    stream_key_res = ivs.create_stream_key(channelArn=channel.get('arn'))
    stream_key = stream_key_res.get('streamKey', {})

    stage_res = ivs_realtime.create_stage(
        name=name,
        tags={
            'app': 'heraldsocial',
            'stream_id': stream_id,
        },
    )
    stage = stage_res.get('stage', {})
    endpoints = stage.get('endpoints') or {}

    playback_url = channel.get('playbackUrl')
    if not playback_url:
        raise IVSProvisioningError('IVS channel did not return a playback URL.')

    return ProvisionedStream(
        provider='ivs',
        playback_url=playback_url,
        ingest_endpoint=channel.get('ingestEndpoint'),
        provider_stream_key=stream_key.get('value'),
        ivs_channel_arn=channel.get('arn'),
        ivs_stage_arn=stage.get('arn'),
        ivs_stage_rtmps_endpoint=endpoints.get('rtmps'),
        ivs_stage_whip_endpoint=endpoints.get('whip'),
    )


def create_host_session(*, stage_arn: str, user_id: str, display_name: str) -> HostSession:
    if not ivs_is_enabled():
        raise IVSProvisioningError('AWS IVS provisioning is not enabled.')

    boto3 = _require_boto3()
    ivs_realtime = _service_client(boto3, 'ivsrealtime', 'ivs-realtime')

    response = ivs_realtime.create_participant_token(
        stageArn=stage_arn,
        duration=1440,
        userId=user_id,
        attributes={
            'display_name': display_name[:100],
            'app': 'heraldsocial',
        },
        capabilities=['PUBLISH', 'SUBSCRIBE'],
    )

    token = response.get('participantToken', {})
    return HostSession(
        token=token.get('token'),
        expires_at=token.get('expirationTime'),
        participant_id=token.get('participantId'),
        stage_arn=stage_arn,
        rtmps_endpoint=(response.get('stageEndpoints') or {}).get('rtmps'),
        whip_endpoint=(response.get('stageEndpoints') or {}).get('whip'),
    )
