from app.normalize import _extract_original_wea_messages, flatten_alert


def test_extract_original_wea_messages_preserves_existing_values_when_later_info_is_empty():
    alert = {
        "originalMessage": """
        <alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
          <info>
            <language>en-US</language>
            <parameter>
              <valueName>CMAMtext</valueName>
              <value>Short English</value>
            </parameter>
            <parameter>
              <valueName>CMAMlongtext</valueName>
              <value>Long English</value>
            </parameter>
          </info>
          <info>
            <language>en-US</language>
            <parameter>
              <valueName>Unrelated</valueName>
              <value>Ignore me</value>
            </parameter>
          </info>
        </alert>
        """
    }

    parsed = _extract_original_wea_messages(alert)

    assert parsed["originalMessage90English"] == "Short English"
    assert parsed["originalMessage360English"] == "Long English"


def test_extract_original_wea_messages_allows_non_empty_replacement_for_same_language():
    alert = {
        "originalMessage": """
        <alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
          <info>
            <language>es-US</language>
            <parameter>
              <valueName>CMAMtext</valueName>
              <value>Texto corto inicial</value>
            </parameter>
          </info>
          <info>
            <language>es-US</language>
            <parameter>
              <valueName>CMAMtext</valueName>
              <value>Texto corto actualizado</value>
            </parameter>
            <parameter>
              <valueName>CMAMlongtext</valueName>
              <value>Texto largo agregado</value>
            </parameter>
          </info>
        </alert>
        """
    }

    parsed = _extract_original_wea_messages(alert)

    assert parsed["originalMessage90Spanish"] == "Texto corto actualizado"
    assert parsed["originalMessage360Spanish"] == "Texto largo agregado"


def test_flatten_alert_does_not_emit_delivery_system_sender_metadata():
    alert = {
        "identifier": "x",
        "sender": "default@example.org",
        "info": [
            {
                "senderName": "Agency One",
                "parameter": [
                    {"valueName": "EAS-ORG", "value": "CIV"},
                    {"valueName": "BLOCKCHANNEL", "value": "NWEM"},
                    {"valueName": "BLOCKCHANNEL", "value": "CMAS"},
                ],
            },
            {
                "senderName": "Agency Two",
                "parameter": [
                    {"valueName": "WEAHandling", "value": "Imminent Threat"},
                ],
            },
        ],
    }

    row = flatten_alert(alert)

    assert "deliverySystems" not in row
    assert "easOrgs" not in row
    assert "easSenders" not in row
    assert "weaSenders" not in row
    assert "nwemSenders" not in row
