# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""Platform-specific configurations for network devices.

This module defines platform configurations using the Platform namedtuple,
which contains commands and configuration settings for various network device
platforms.

The Platform namedtuple includes:
    get_config_commands: Tuple of commands to retrieve running configuration
    supports_commit: Boolean indicating if configuration changes require commit
    pre_config_hook: Optional callable to execute before configuration
    post_config_hook: Optional callable to execute after configuration

These configurations are used by the broker's get_config and set_config
functions to determine behavior based on the device platform.

Platform Constants:
    Each constant is a Platform instance for a specific network OS
    Examples: CISCO_IOS, ARISTA_EOS, JUNIPER_JUNOS, etc.
"""

from collections import namedtuple

__all__ = ("Platform",)


Platform = namedtuple(
    "Platform",
    ["get_config_commands", "supports_commit", "pre_config_hook", "post_config_hook"],
    defaults=[(), False, None, None],
)

# Platform constants
A10 = Platform(get_config_commands=("show running-config",))

ACCEDIAN = Platform(get_config_commands=("show running-config",))

ADTRAN_OS = Platform(get_config_commands=("show running-config",))

ADVA_FSP150F2 = Platform(get_config_commands=("show running-config",))

ADVA_FSP150F3 = Platform(get_config_commands=("show running-config",))

ALAXALA_AX26S = Platform(get_config_commands=("show running-config",))

ALAXALA_AX36S = Platform(get_config_commands=("show running-config",))

ALCATEL_AOS = Platform(get_config_commands=("show configuration snapshot",))

ALCATEL_SROS = Platform(
    get_config_commands=("admin display-config",), supports_commit=True
)

ALLIED_TELESIS_AWPLUS = Platform(get_config_commands=("show running-config",))

APRESIA_AEOS = Platform(get_config_commands=("show running-config",))

ARISTA_EOS = Platform(get_config_commands=("show running-config",))

ARRIS_CER = Platform(get_config_commands=("show running-config",))

ARUBA_AOSCX = Platform(get_config_commands=("show running-config",))

ARUBA_OS = Platform(get_config_commands=("show running-config",))

ARUBA_OSSWITCH = Platform(get_config_commands=("show running-config",))

ARUBA_PROCURVE = Platform(get_config_commands=("show running-config",))

ASTERFUSION_ASTERNOS = Platform(get_config_commands=("show running-config",))

AUDIOCODE_66 = Platform(get_config_commands=("show running-config",))

AUDIOCODE_72 = Platform(get_config_commands=("show running-config",))

AUDIOCODE_SHELL = Platform(get_config_commands=("show running-config",))

AVAYA_ERS = Platform(get_config_commands=("show running-config",))

AVAYA_VSP = Platform(get_config_commands=("show running-config",))

BINTEC_BOSS = Platform(get_config_commands=("show running-config",))

BROADCOM_ICOS = Platform(get_config_commands=("show running-config",))

BROCADE_FASTIRON = Platform(get_config_commands=("show running-config",))

BROCADE_FOS = Platform(get_config_commands=("configshow",))

BROCADE_NETIRON = Platform(get_config_commands=("show running-config",))

BROCADE_NOS = Platform(get_config_commands=("show running-config",))

BROCADE_VDX = Platform(get_config_commands=("show running-config",))

BROCADE_VYOS = Platform(
    get_config_commands=("show configuration",), supports_commit=True
)

CALIX_B6 = Platform(get_config_commands=("show running-config",))

CASA_CMTS = Platform(get_config_commands=("show running-config",))

CDOT_CROS = Platform(get_config_commands=("show running-config",))

CENTEC_OS = Platform(get_config_commands=("show running-config",))

CHECKPOINT_GAIA = Platform(
    get_config_commands=("show configuration",), supports_commit=True
)

CIENA_SAOS = Platform(get_config_commands=("configuration show",), supports_commit=True)

CIENA_SAOS10 = Platform(
    get_config_commands=("configuration show",), supports_commit=True
)

CIENA_WAVESERVER = Platform(get_config_commands=("software show running-config",))

CISCO_APIC = Platform(get_config_commands=("show running-config",))

CISCO_ASA = Platform(get_config_commands=("show running-config",))

CISCO_FTD = Platform(get_config_commands=("show running-config",))

CISCO_IOS = Platform(get_config_commands=("show running-config",))

CISCO_IOSXE = Platform(get_config_commands=("show running-config",))

CISCO_IOSXR = Platform(
    get_config_commands=("show running-config",), supports_commit=True
)

CISCO_NXOS = Platform(get_config_commands=("show running-config",))

CISCO_S200 = Platform(get_config_commands=("show running-config",))

CISCO_S300 = Platform(get_config_commands=("show running-config",))

CISCO_TP = Platform(get_config_commands=("show running-config",))

CISCO_VIPTELA = Platform(get_config_commands=("show running-config",))

CISCO_WLC = Platform(get_config_commands=("show running-config",))

CISCO_XE = Platform(get_config_commands=("show running-config",))

CISCO_XR = Platform(get_config_commands=("show running-config",), supports_commit=True)

CLOUDGENIX_ION = Platform(get_config_commands=("show running-config",))

CORELIGHT_LINUX = Platform(get_config_commands=("cat /etc/network/interfaces",))

CORIANT = Platform(get_config_commands=("show running-config",))

CUMULUS_LINUX = Platform(get_config_commands=("net show configuration",))

DELL_DNOS9 = Platform(get_config_commands=("show running-config",))

DELL_FORCE10 = Platform(get_config_commands=("show running-config",))

DELL_ISILON = Platform(get_config_commands=("isi config",))

DELL_OS10 = Platform(get_config_commands=("show running-config",))

DELL_OS6 = Platform(get_config_commands=("show running-config",))

DELL_OS9 = Platform(get_config_commands=("show running-config",))

DELL_POWERCONNECT = Platform(get_config_commands=("show running-config",))

DELL_SONIC = Platform(get_config_commands=("show runningconfiguration all",))

DIGI_TRANSPORT = Platform(get_config_commands=("show running-config",))

DLINK_DS = Platform(get_config_commands=("show running-config",))

EDGECORE_SONIC = Platform(get_config_commands=("show running-config",))

EKINOPS_EK360 = Platform(get_config_commands=("show running-config",))

ELTEX = Platform(get_config_commands=("show running-config",))

ELTEX_ESR = Platform(get_config_commands=("show running-config",))

ENDACE = Platform(get_config_commands=("show running-config",))

ENTERASYS = Platform(get_config_commands=("show running-config",))

ERICSSON_IPOS = Platform(get_config_commands=("show running-config",))

ERICSSON_MLTN63 = Platform(get_config_commands=("show running-config",))

ERICSSON_MLTN66 = Platform(get_config_commands=("show running-config",))

EXTREME = Platform(get_config_commands=("show configuration",))

EXTREME_ERS = Platform(get_config_commands=("show running-config",))

EXTREME_EXOS = Platform(get_config_commands=("show configuration",))

EXTREME_NETIRON = Platform(get_config_commands=("show running-config",))

EXTREME_NOS = Platform(get_config_commands=("show running-config",))

EXTREME_SLX = Platform(get_config_commands=("show running-config",))

EXTREME_TIERRA = Platform(get_config_commands=("show running-config",))

EXTREME_VDX = Platform(get_config_commands=("show running-config",))

EXTREME_VSP = Platform(get_config_commands=("show running-config",))

EXTREME_WING = Platform(get_config_commands=("show running-config",))

F5_LINUX = Platform(get_config_commands=("tmsh list",))

F5_LTM = Platform(get_config_commands=("tmsh list ltm",))

F5_TMSH = Platform(get_config_commands=("list",))

FIBERSTORE_FSOS = Platform(get_config_commands=("show running-config",))

FIBERSTORE_FSOSV2 = Platform(get_config_commands=("show running-config",))

FIBERSTORE_NETWORKOS = Platform(get_config_commands=("show running-config",))

FLEXVNF = Platform(get_config_commands=("show running-config",))

FORTINET = Platform(get_config_commands=("show full-configuration",))

GARDEROS_GRS = Platform(get_config_commands=("show running-config",))

GENERIC = Platform(get_config_commands=("show running-config",))

GENERIC_TERMSERVER = Platform(get_config_commands=("show running-config",))

H3C_COMWARE = Platform(get_config_commands=("display current-configuration",))

HILLSTONE_STONEOS = Platform(get_config_commands=("show running-config",))

HP_COMWARE = Platform(get_config_commands=("display current-configuration",))

HP_PROCURVE = Platform(get_config_commands=("show running-config",))

HUAWEI = Platform(get_config_commands=("display current-configuration",))

HUAWEI_OLT = Platform(get_config_commands=("display current-configuration",))

HUAWEI_SMARTAX = Platform(get_config_commands=("display current-configuration",))

HUAWEI_SMARTAXMMI = Platform(get_config_commands=("display current-configuration",))

HUAWEI_VRP = Platform(get_config_commands=("display current-configuration",))

HUAWEI_VRPV8 = Platform(get_config_commands=("display current-configuration",))

INFINERA_PACKET = Platform(get_config_commands=("show running-config",))

IPINFUSION_OCNOS = Platform(get_config_commands=("show running-config",))

JUNIPER = Platform(get_config_commands=("show configuration",), supports_commit=True)

JUNIPER_JUNOS = Platform(
    get_config_commands=("show configuration",), supports_commit=True
)

JUNIPER_SCREENOS = Platform(get_config_commands=("get config",))

KEYMILE = Platform(get_config_commands=("show running-config",))

KEYMILE_NOS = Platform(get_config_commands=("show running-config",))

LANCOM_LCOSSX4 = Platform(get_config_commands=("show running-config",))

LINUX = Platform(get_config_commands=("cat /etc/network/interfaces",))

MAIPU = Platform(get_config_commands=("show running-config",))

MELLANOX = Platform(get_config_commands=("show running-config",))

MELLANOX_MLNXOS = Platform(get_config_commands=("show running-config",))

MIKROTIK_ROUTEROS = Platform(get_config_commands=("/export",))

MIKROTIK_SWITCHOS = Platform(get_config_commands=("/export",))

MOXA_NOS = Platform(get_config_commands=("show running-config",))

MRV_LX = Platform(get_config_commands=("show running-config",))

MRV_OPTISWITCH = Platform(get_config_commands=("show running-config",))

NEC_IX = Platform(get_config_commands=("show running-config",))

NETAPP_CDOT = Platform(
    get_config_commands=(
        "vserver show",
        "network interface show",
    )
)

NETGEAR_PROSAFE = Platform(get_config_commands=("show running-config",))

NETSCALER = Platform(get_config_commands=("show running-config",))

NOKIA_SRL = Platform(get_config_commands=("info from state",), supports_commit=True)

NOKIA_SROS = Platform(
    get_config_commands=("admin display-config",), supports_commit=True
)

ONEACCESS_ONEOS = Platform(get_config_commands=("show running-config",))

OVS_LINUX = Platform(get_config_commands=("ovs-vsctl show",))

PALOALTO_PANOS = Platform(get_config_commands=("show config running",))

PLURIBUS = Platform(get_config_commands=("show running-config",))

QUANTA_MESH = Platform(get_config_commands=("show running-config",))

RAD_ETX = Platform(get_config_commands=("show running-config",))

RAISECOM_ROAP = Platform(get_config_commands=("show running-config",))

RUCKUS_FASTIRON = Platform(get_config_commands=("show running-config",))

RUIJIE_OS = Platform(get_config_commands=("show running-config",))

SILVERPEAK_VXOA = Platform(get_config_commands=("show running-config",))

SIXWIND_OS = Platform(get_config_commands=("show running-config",))

SOPHOS_SFOS = Platform(get_config_commands=("show running-config",))

SUPERMICRO_SMIS = Platform(get_config_commands=("show running-config",))

TELCOSYSTEMS_BINOS = Platform(get_config_commands=("show running-config",))

TELDAT_CIT = Platform(get_config_commands=("show running-config",))

TPLINK_JETSTREAM = Platform(get_config_commands=("show running-config",))

UBIQUITI_EDGE = Platform(
    get_config_commands=("show configuration",), supports_commit=True
)

UBIQUITI_EDGEROUTER = Platform(
    get_config_commands=("show configuration",), supports_commit=True
)

UBIQUITI_EDGESWITCH = Platform(get_config_commands=("show running-config",))

UBIQUITI_UNIFISWITCH = Platform(get_config_commands=("show running-config",))

VERTIV_MPH = Platform(get_config_commands=("show running-config",))

VYATTA_VYOS = Platform(
    get_config_commands=("show configuration",), supports_commit=True
)

VYOS = Platform(get_config_commands=("show configuration",), supports_commit=True)

WATCHGUARD_FIREWARE = Platform(get_config_commands=("show running-config",))

YAMAHA = Platform(get_config_commands=("show running-config",))

ZTE_ZXROS = Platform(get_config_commands=("show running-config",))

ZYXEL_OS = Platform(get_config_commands=("show running-config",))
