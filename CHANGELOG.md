# Change Log
All notable changes to this project will be documented in this file.

## 1.5.1 2023-12-13
### Added
- Search API for Projects
- Bug fix for duplicate variable ids

## 1.5.0 2023-08-16
### Added
- nothing added

## 1.4.0 2023-07-14
### Added
- nothing added

## 1.3.0 2023-03-10
### Added
- Alerts added Deadman checks for no data incoming for a set period
- Alerts added support for Tapis Jobs as an action

### Changed
- fixed some issues with OpenAPI specification affecting tapipy and making it reflect resources better
- fixed minor bugs with Variable resources

### Removed
- nothing removed 

## 1.2.0- 2022-6-7
### Added
- Support for newly created projects data written to individual buckets for security
- Support for project,site,instrument,variable skip and limit parameters in listing
- Alerts support added for Influx2 for Actors, Discord, Slack and generic webhooks
- Alerts has default threshold template built in for users to access

### Changed
- Newly Created Projects data no longer written to central streams bucket, legacy projects will still use streams bucket
- All resources have created_at field

### Removed
- nothing removed

## 1.1.0- 2022-1-27 
### Added
- nothing added

### Changed
- Influx2 database support for measurements storage was added

### Removed
- Alerts support is removed in 1.1.0
- Influx1 support was removed

## 1.0.0 - 2021-7-22 
### Added
-  Initial Release 

### Changed
- No change.

### Removed
- No change.


## 1.0.0-RC1 - 2021-7-22
### Added
- Initial Release candidate 1.

### Changed
- No change.

### Removed
- No change.
