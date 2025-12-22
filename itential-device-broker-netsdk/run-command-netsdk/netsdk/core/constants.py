# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""Platform-specific command constants for network devices.

This module defines command tuples for retrieving configuration from various
network device platforms. Each platform constant contains the commands needed
to retrieve the running configuration.

These constants are used by the broker's get_config function to determine
which commands to execute based on the device platform.

Platform Constants:
    Each constant is a tuple of commands for a specific network OS
    Examples: CISCO_IOS, ARISTA_EOS, JUNIPER_JUNOS, etc.
"""

# Platform constants
A10 = ("show running-config",)

ACCEDIAN = ("show running-config",)

ADTRAN_OS = ("show running-config",)

ADVA_FSP150F2 = ("show running-config",)

ADVA_FSP150F3 = ("show running-config",)

ALAXALA_AX26S = ("show running-config",)

ALAXALA_AX36S = ("show running-config",)

ALCATEL_AOS = ("show configuration snapshot",)

ALCATEL_SROS = ("admin display-config",)

ALLIED_TELESIS_AWPLUS = ("show running-config",)

APRESIA_AEOS = ("show running-config",)

ARISTA_EOS = ("show running-config",)

ARRIS_CER = ("show running-config",)

ARUBA_AOSCX = ("show running-config",)

ARUBA_OS = ("show running-config",)

ARUBA_OSSWITCH = ("show running-config",)

ARUBA_PROCURVE = ("show running-config",)

ASTERFUSION_ASTERNOS = ("show running-config",)

AUDIOCODE_66 = ("show running-config",)

AUDIOCODE_72 = ("show running-config",)

AUDIOCODE_SHELL = ("show running-config",)

AVAYA_ERS = ("show running-config",)

AVAYA_VSP = ("show running-config",)

BINTEC_BOSS = ("show running-config",)

BROADCOM_ICOS = ("show running-config",)

BROCADE_FASTIRON = ("show running-config",)

BROCADE_FOS = ("configshow",)

BROCADE_NETIRON = ("show running-config",)

BROCADE_NOS = ("show running-config",)

BROCADE_VDX = ("show running-config",)

BROCADE_VYOS = ("show configuration",)

CALIX_B6 = ("show running-config",)

CASA_CMTS = ("show running-config",)

CDOT_CROS = ("show running-config",)

CENTEC_OS = ("show running-config",)

CHECKPOINT_GAIA = ("show configuration",)

CIENA_SAOS = ("configuration show",)

CIENA_SAOS10 = ("configuration show",)

CIENA_WAVESERVER = ("software show running-config",)

CISCO_APIC = ("show running-config",)

CISCO_ASA = ("show running-config",)

CISCO_FTD = ("show running-config",)

CISCO_IOS = ("show running-config",)

CISCO_IOSXE = ("show running-config",)

CISCO_IOSXR = ("show running-config",)

CISCO_NXOS = ("show running-config",)

CISCO_S200 = ("show running-config",)

CISCO_S300 = ("show running-config",)

CISCO_TP = ("show running-config",)

CISCO_VIPTELA = ("show running-config",)

CISCO_WLC = ("show running-config",)

CISCO_XE = ("show running-config",)

CISCO_XR = ("show running-config",)

CLOUDGENIX_ION = ("show running-config",)

CORELIGHT_LINUX = ("cat /etc/network/interfaces",)

CORIANT = ("show running-config",)

CUMULUS_LINUX = ("net show configuration",)

DELL_DNOS9 = ("show running-config",)

DELL_FORCE10 = ("show running-config",)

DELL_ISILON = ("isi config",)

DELL_OS10 = ("show running-config",)

DELL_OS6 = ("show running-config",)

DELL_OS9 = ("show running-config",)

DELL_POWERCONNECT = ("show running-config",)

DELL_SONIC = ("show runningconfiguration all",)

DIGI_TRANSPORT = ("show running-config",)

DLINK_DS = ("show running-config",)

EDGECORE_SONIC = ("show running-config",)

EKINOPS_EK360 = ("show running-config",)

ELTEX = ("show running-config",)

ELTEX_ESR = ("show running-config",)

ENDACE = ("show running-config",)

ENTERASYS = ("show running-config",)

ERICSSON_IPOS = ("show running-config",)

ERICSSON_MLTN63 = ("show running-config",)

ERICSSON_MLTN66 = ("show running-config",)

EXTREME = ("show configuration",)

EXTREME_ERS = ("show running-config",)

EXTREME_EXOS = ("show configuration",)

EXTREME_NETIRON = ("show running-config",)

EXTREME_NOS = ("show running-config",)

EXTREME_SLX = ("show running-config",)

EXTREME_TIERRA = ("show running-config",)

EXTREME_VDX = ("show running-config",)

EXTREME_VSP = ("show running-config",)

EXTREME_WING = ("show running-config",)

F5_LINUX = ("tmsh list",)

F5_LTM = ("tmsh list ltm",)

F5_TMSH = ("list",)

FIBERSTORE_FSOS = ("show running-config",)

FIBERSTORE_FSOSV2 = ("show running-config",)

FIBERSTORE_NETWORKOS = ("show running-config",)

FLEXVNF = ("show running-config",)

FORTINET = ("show full-configuration",)

GARDEROS_GRS = ("show running-config",)

GENERIC = ("show running-config",)

GENERIC_TERMSERVER = ("show running-config",)

H3C_COMWARE = ("display current-configuration",)

HILLSTONE_STONEOS = ("show running-config",)

HP_COMWARE = ("display current-configuration",)

HP_PROCURVE = ("show running-config",)

HUAWEI = ("display current-configuration",)

HUAWEI_OLT = ("display current-configuration",)

HUAWEI_SMARTAX = ("display current-configuration",)

HUAWEI_SMARTAXMMI = ("display current-configuration",)

HUAWEI_VRP = ("display current-configuration",)

HUAWEI_VRPV8 = ("display current-configuration",)

INFINERA_PACKET = ("show running-config",)

IPINFUSION_OCNOS = ("show running-config",)

JUNIPER = ("show configuration",)

JUNIPER_JUNOS = ("show configuration",)

JUNIPER_SCREENOS = ("get config",)

KEYMILE = ("show running-config",)

KEYMILE_NOS = ("show running-config",)

LANCOM_LCOSSX4 = ("show running-config",)

LINUX = ("cat /etc/network/interfaces",)

MAIPU = ("show running-config",)

MELLANOX = ("show running-config",)

MELLANOX_MLNXOS = ("show running-config",)

MIKROTIK_ROUTEROS = ("/export",)

MIKROTIK_SWITCHOS = ("/export",)

MOXA_NOS = ("show running-config",)

MRV_LX = ("show running-config",)

MRV_OPTISWITCH = ("show running-config",)

NEC_IX = ("show running-config",)

NETAPP_CDOT = (
    "vserver show",
    "network interface show",
)

NETGEAR_PROSAFE = ("show running-config",)

NETSCALER = ("show running-config",)

NOKIA_SRL = ("info from state",)

NOKIA_SROS = ("admin display-config",)

ONEACCESS_ONEOS = ("show running-config",)

OVS_LINUX = ("ovs-vsctl show",)

PALOALTO_PANOS = ("show config running",)

PLURIBUS = ("show running-config",)

QUANTA_MESH = ("show running-config",)

RAD_ETX = ("show running-config",)

RAISECOM_ROAP = ("show running-config",)

RUCKUS_FASTIRON = ("show running-config",)

RUIJIE_OS = ("show running-config",)

SILVERPEAK_VXOA = ("show running-config",)

SIXWIND_OS = ("show running-config",)

SOPHOS_SFOS = ("show running-config",)

SUPERMICRO_SMIS = ("show running-config",)

TELCOSYSTEMS_BINOS = ("show running-config",)

TELDAT_CIT = ("show running-config",)

TPLINK_JETSTREAM = ("show running-config",)

UBIQUITI_EDGE = ("show configuration",)

UBIQUITI_EDGEROUTER = ("show configuration",)

UBIQUITI_EDGESWITCH = ("show running-config",)

UBIQUITI_UNIFISWITCH = ("show running-config",)

VERTIV_MPH = ("show running-config",)

VYATTA_VYOS = ("show configuration",)

VYOS = ("show configuration",)

WATCHGUARD_FIREWARE = ("show running-config",)

YAMAHA = ("show running-config",)

ZTE_ZXROS = ("show running-config",)

ZYXEL_OS = ("show running-config",)
