[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/J-Lindvig/Fuelprices_DK)
![GitHub all releases](https://img.shields.io/github/downloads/J-Lindvig/Fuelprices_DK/total)
![GitHub last commit](https://img.shields.io/github/last-commit/J-Lindvig/Fuelprices_DK)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/J-Lindvig/Fuelprices_DK)
[![Buy me a coffee](https://img.shields.io/static/v1.svg?label=Buy%20me%20a%20coffee&message=🥨&color=black&logo=buy%20me%20a%20coffee&logoColor=white&labelColor=6f4e37)](https://www.buymeacoffee.com/apptoo)

# Fuelprices DK
## Introduction
With Fuelprices_DK it is possible to track fuelprices in Denmark.

## Installation
### HACS
This integration has been approved to the default HACS repository
### Custom integration in HACS
https://hacs.xyz/docs/faq/custom_repositories

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
