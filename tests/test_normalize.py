from app.normalize import _extract_original_wea_messages


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
