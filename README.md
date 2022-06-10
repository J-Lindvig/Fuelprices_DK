# Fuelprices DK
## Introduction
With Fuelprices_DK it is possible to track fuelprices in Denmark.

## Installation
### Custom integration in HACS
https://hacs.xyz/docs/faq/custom_repositories
### HACS approved integration
Coming soon....!!

## Configuration
In the default configuration it will track the following fueltypes:
- Octane 95
- Octane 95+ (additives)
- Octane 100
- Diesel
- Diesel+ (additives)

From these fuelcompanies:
- Circle K
- F24
- Go'On
- ingo
- OIL! tank & go
- OK
- Q8
- Shell

## Configuration
```yaml
fuelprices_dk:
  # Optional entries
  companies:
  # possible values are: circlek, f24, goon, ingo, oil, ok, q8 and shell
    - ok
    - shell
  fueltypes:
  # Possible values are: oktan 95, oktan 95+, oktan 100, diesel, diesel+
    - oktan 95
    - diesel
```
