"""General ADF-Pipeline Setup."""

import os

import esphome.codegen as cg
from esphome.components.esp32 import add_idf_component
from esphome.components import esp32
import esphome.config_validation as cv
from esphome.core import coroutine_with_priority

CODEOWNERS = ["@gnumpi"]
DEPENDENCIES = []

IS_PLATFORM_COMPONENT = True

CONF_ADF_COMPONENT_TYPE = "type"
CONF_ADF_PIPELINE = "pipeline"
CONF_ADF_KEEP_PIPELINE_ALIVE = "keep_pipeline_alive"

esp_adf_ns = cg.esphome_ns.namespace("esp_adf")
ADFPipelineController = esp_adf_ns.class_("ADFPipelineController")

ADFPipelineElement = esp_adf_ns.class_("ADFPipelineElement")
ADFPipelineSink = esp_adf_ns.class_("ADFPipelineSinkElement")
ADFPipelineSource = esp_adf_ns.class_("ADFPipelineSourceElement")


# Pipeline Controller

COMPONENT_TYPES = ["sink", "source", "filter"]
SELF_DESCRIPTORS = ["this", "source", "sink", "self"]
ADF_PIPELINE_CONTROLLER_SCHEMA = cv.Schema(
    {
        cv.Optional(CONF_ADF_COMPONENT_TYPE): cv.one_of(*COMPONENT_TYPES),
        cv.Optional(CONF_ADF_KEEP_PIPELINE_ALIVE, default=False): cv.boolean,
        cv.Optional(CONF_ADF_PIPELINE): cv.ensure_list(
            cv.Any(
                cv.one_of(*SELF_DESCRIPTORS),
                cv.use_id(ADFPipelineElement),
            )
        ),
    }
)


async def setup_pipeline_controller(cntrl: ADFPipelineController, config: dict) -> None:
    """Set controller parameter and register elements to pipeline."""

    cg.add(cntrl.set_keep_alive(config[CONF_ADF_KEEP_PIPELINE_ALIVE]))

    if CONF_ADF_PIPELINE in config:
        for comp_id in config[CONF_ADF_PIPELINE]:
            if comp_id not in SELF_DESCRIPTORS:
                comp = await cg.get_variable(comp_id)
                cg.add(cntrl.add_element_to_pipeline(comp))
            else:
                cg.add(cntrl.append_own_elements())


# Pipeline Elements


def construct_pipeline_element_config_schema(config_schema_out, config_schema_in):
    """"""
    return cv.typed_schema(
        {
            "sink": config_schema_out,
            "source": config_schema_in,
        },
        lower=True,
        space="-",
        default_type="sink",
    )


ADF_PIPELINE_ELEMENT_SCHEMA = cv.Schema({})


# ADF-Pipeline component global settings


@coroutine_with_priority(55.0)
async def to_code(config):
    cg.add_define("USE_ESP_ADF")

    cg.add_platformio_option("build_unflags", "-Wl,--end-group")

    cg.add_platformio_option(
        "board_build.embed_txtfiles", "components/dueros_service/duer_profile"
    )

    esp32.add_idf_sdkconfig_option("CONFIG_ESP_TLS_INSECURE", True)
    esp32.add_idf_sdkconfig_option("CONFIG_ESP_TLS_SKIP_SERVER_CERT_VERIFY", True)

    esp32.add_extra_script(
        "pre",
        "apply_adf_patches.py",
        os.path.join(os.path.dirname(__file__), "apply_adf_patches.py.script"),
    )

    esp32.add_extra_build_file(
        "esp_adf_patches/idf_v4.4_freertos.patch",
        "https://github.com/espressif/esp-adf/raw/v2.5/idf_patches/idf_v4.4_freertos.patch",
    )

    add_idf_component(
        name="mdns",
        repo="https://github.com/espressif/esp-adf.git",
        ref="v2.5",
        path="components",
        submodules=["components/esp-adf-libs", "components/esp-sr"],
        components=[
            "audio_pipeline",
            "audio_sal",
            "esp-adf-libs",
            "esp-sr",
            "dueros_service",
            "clouds",
            "audio_stream",
            "audio_board",
            "esp_peripherals",
            "audio_hal",
            "display_service",
            "esp_dispatcher",
            "esp_actions",
            "wifi_service",
            "audio_recorder",
            "tone_partition",
        ],
    )
