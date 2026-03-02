# Data Model: OpenAPI ER Diagram Documentation

Source: `openapi.json` (WHOOP API v2.0.0)

## Entities

### User Domain

**UserBasicProfile**
| Attribute  | Type   | Required |
|-----------|--------|----------|
| user_id    | long   | Yes      |
| email      | string | Yes      |
| first_name | string | Yes      |
| last_name  | string | Yes      |

**UserBodyMeasurement**
| Attribute       | Type  | Required |
|----------------|-------|----------|
| height_meter    | float | Yes      |
| weight_kilogram | float | Yes      |
| max_heart_rate  | int   | Yes      |

### Cycle Domain

**Cycle**
| Attribute       | Type     | Required |
|----------------|----------|----------|
| id              | long     | Yes      |
| user_id         | long     | Yes      |
| created_at      | datetime | Yes      |
| updated_at      | datetime | Yes      |
| start           | datetime | Yes      |
| end             | datetime | No       |
| timezone_offset | string   | Yes      |
| score_state     | enum     | Yes      |

Relationships: has optional CycleScore

**CycleScore**
| Attribute          | Type  | Required |
|-------------------|-------|----------|
| strain             | float | Yes      |
| kilojoule          | float | Yes      |
| average_heart_rate | int   | Yes      |
| max_heart_rate     | int   | Yes      |

### Sleep Domain

**Sleep**
| Attribute       | Type     | Required |
|----------------|----------|----------|
| id              | uuid     | Yes      |
| cycle_id        | long     | Yes      |
| v1_id           | long     | No       |
| user_id         | long     | Yes      |
| created_at      | datetime | Yes      |
| updated_at      | datetime | Yes      |
| start           | datetime | Yes      |
| end             | datetime | Yes      |
| timezone_offset | string   | Yes      |
| nap             | boolean  | Yes      |
| score_state     | enum     | Yes      |

Relationships: has optional SleepScore, belongs to Cycle

**SleepScore**
| Attribute                      | Type  | Required |
|-------------------------------|-------|----------|
| respiratory_rate               | float | No       |
| sleep_performance_percentage   | float | No       |
| sleep_consistency_percentage   | float | No       |
| sleep_efficiency_percentage    | float | No       |

Relationships: has SleepStageSummary, has SleepNeeded

**SleepStageSummary**
| Attribute                       | Type | Required |
|--------------------------------|------|----------|
| total_in_bed_time_milli         | int  | Yes      |
| total_awake_time_milli          | int  | Yes      |
| total_no_data_time_milli        | int  | Yes      |
| total_light_sleep_time_milli    | int  | Yes      |
| total_slow_wave_sleep_time_milli| int  | Yes      |
| total_rem_sleep_time_milli      | int  | Yes      |
| sleep_cycle_count               | int  | Yes      |
| disturbance_count               | int  | Yes      |

**SleepNeeded**
| Attribute                     | Type | Required |
|------------------------------|------|----------|
| baseline_milli                | long | Yes      |
| need_from_sleep_debt_milli    | long | Yes      |
| need_from_recent_strain_milli | long | Yes      |
| need_from_recent_nap_milli    | long | Yes      |

### Recovery Domain

**Recovery**
| Attribute   | Type     | Required |
|------------|----------|----------|
| cycle_id    | long     | Yes      |
| sleep_id    | uuid     | Yes      |
| user_id     | long     | Yes      |
| created_at  | datetime | Yes      |
| updated_at  | datetime | Yes      |
| score_state | enum     | Yes      |

Relationships: has optional RecoveryScore, belongs to Cycle and Sleep

**RecoveryScore**
| Attribute         | Type    | Required |
|------------------|---------|----------|
| user_calibrating  | boolean | Yes      |
| recovery_score    | float   | Yes      |
| resting_heart_rate| float   | Yes      |
| hrv_rmssd_milli   | float   | Yes      |
| spo2_percentage   | float   | No       |
| skin_temp_celsius | float   | No       |

### Workout Domain

**WorkoutV2**
| Attribute       | Type     | Required |
|----------------|----------|----------|
| id              | uuid     | Yes      |
| v1_id           | long     | No       |
| user_id         | long     | Yes      |
| created_at      | datetime | Yes      |
| updated_at      | datetime | Yes      |
| start           | datetime | Yes      |
| end             | datetime | Yes      |
| timezone_offset | string   | Yes      |
| sport_name      | string   | Yes      |
| score_state     | enum     | Yes      |
| sport_id        | int      | No       |

Relationships: has optional WorkoutScore

**WorkoutScore**
| Attribute            | Type  | Required |
|---------------------|-------|----------|
| strain               | float | Yes      |
| average_heart_rate   | int   | Yes      |
| max_heart_rate       | int   | Yes      |
| kilojoule            | float | Yes      |
| percent_recorded     | float | Yes      |
| distance_meter       | float | No       |
| altitude_gain_meter  | float | No       |
| altitude_change_meter| float | No       |

Relationships: has ZoneDurations

**ZoneDurations**
| Attribute       | Type | Required |
|----------------|------|----------|
| zone_zero_milli | long | Yes      |
| zone_one_milli  | long | Yes      |
| zone_two_milli  | long | Yes      |
| zone_three_milli| long | Yes      |
| zone_four_milli | long | Yes      |
| zone_five_milli | long | Yes      |

### Utility Domain

**ActivityIdMappingResponse**
| Attribute      | Type | Required |
|---------------|------|----------|
| v2_activity_id | uuid | Yes      |

Standalone entity (no relationships to other domain entities).

## Relationships

| From             | To                  | Cardinality | Via Field  | Description                          |
|-----------------|---------------------|-------------|------------|--------------------------------------|
| UserBasicProfile | Cycle               | one-to-many | user_id    | A user has many cycles               |
| UserBasicProfile | Sleep               | one-to-many | user_id    | A user has many sleeps               |
| UserBasicProfile | Recovery            | one-to-many | user_id    | A user has many recoveries           |
| UserBasicProfile | WorkoutV2           | one-to-many | user_id    | A user has many workouts             |
| Cycle            | CycleScore          | one-to-zero-or-one | score | A cycle optionally has a score |
| Cycle            | Sleep               | one-to-many | cycle_id   | A cycle contains sleeps              |
| Cycle            | Recovery            | one-to-zero-or-one | cycle_id | A cycle has at most one recovery |
| Sleep            | SleepScore          | one-to-zero-or-one | score | A sleep optionally has a score   |
| Sleep            | Recovery            | one-to-zero-or-one | sleep_id | A sleep has at most one recovery |
| SleepScore       | SleepStageSummary   | one-to-one  | stage_summary | Score contains stage summary   |
| SleepScore       | SleepNeeded         | one-to-one  | sleep_needed  | Score contains sleep needed    |
| Recovery         | RecoveryScore       | one-to-zero-or-one | score | Recovery optionally has a score |
| WorkoutV2        | WorkoutScore        | one-to-zero-or-one | score | Workout optionally has a score |
| WorkoutScore     | ZoneDurations       | one-to-one  | zone_durations | Score contains zone durations |

## Excluded Entities (Pagination Wrappers)

These are excluded from the ER diagram per FR-008:
- PaginatedCycleResponse (wraps Cycle[])
- PaginatedSleepResponse (wraps Sleep[])
- RecoveryCollection (wraps Recovery[])
- WorkoutCollection (wraps WorkoutV2[])
