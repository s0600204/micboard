### Discovery of UHF-R devices

(My thanks to [Thomas Mathieson](https://github.com/space928) for his
[WirelessMicSuiteServer](https://github.com/space928/WirelessMicSuiteServer)
project that helped join a lot of dots.)

Shure UHF-R devices (UR4S and UR4D) use a different discovery mechanism
than other Shure devices. Notably, they don't use the ACN-based
multicast method, but rather a broadcast method on port 2201.

In fact, UHF-R devices seem to primarily communicate using a protocol
that Mr Matheison refers to as `SNet`. I don't know if this is an
official name, or a moniker he gave it, but either way, `SNet`
messages are formatted as follows:

```
  04 00 79 ad  15 e1 11 80  00 00  00 03  00 12  23 d1  2a 20 4d 45 54 45 52 20 31 20 41 4c 4c 20 31 30 20 2a
  [---to----]  [--from---]  [pad]  [typ]  [len]  [chk]  [----------------------message----------------------]
```

* `to`

  4-octet sequence identifying the intended recipient.

  For Discovery messages, which are intended for anyone listening, this
  is `FF FF FF FF`.

* `from`

  4-octet sequence identifying the sender.

* `pad`

  Two null octets.

* `typ`

  The type of message being conveyed. At present, three types are known:

  1 - Discovery message
  
  3 - Normal message
  
  4 - Special message

* `len`

  Length of the message payload.

* `chk`

  Checksum value.

* `message`

  The message payload.

  For Normal messages, the payload is identical to messages ordinarily
  conveyed via unicast UDP on port `2202`.

  For Discovery messages, the message is always eight octets in length -
  `00 01 00 01` followed by the `from` sequence. For example:

  ```
  00 01 00 01 04 00 79 ad
  ```

As the devices are capable of communicating device status and
information over port `2202`, we don't need to use `SNet`'s Normal
messages. This simplifies implementation.

However, there is something to be careful of here: Wireless Workbench
also emits a `SNet` discovery message.

At this time, it is unclear how the `to` and `from` identifiers are
generated.

For the singular UR4D receiver I have to test with, its identifier is
`04 00 79 AD`. The last three octets here also happen to be the last
three octets of the receiver's MAC address. What the first octet could
represent is unclear, but it (and the rest of the identifier) remains
consistent between device power cycles.

However, the most recent identifier I've observed Wireless Workbench 6
to use is `15 e1 11 80`, which bears no resemblance to the MAC or IPv4
addresses of any of the network interfaces that the software is running
on.
