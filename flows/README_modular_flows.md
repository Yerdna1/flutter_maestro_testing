# Modular Maestro Flows

This directory contains a modular flow structure that separates coordinate analysis from test execution.

## Structure

```
flows/
├── objednavka_main.yaml          # Main orchestrator flow with environment variables
├── objednavka.yaml               # Original monolithic flow (kept for reference)
└── subflows/
    ├── login_flow.yaml           # Login sequence
    ├── doctor_search_flow.yaml   # Doctor search functionality
    ├── patient_id_flow.yaml      # Patient ID input
    ├── new_order_flow.yaml       # New order creation
    └── category_selection_flow.yaml # Test category selection
```

## Usage Workflow

### 1. Analyze Screenshots and Update Coordinates

```bash
# Run coordinate analysis on existing screenshots
python update_flow_coordinates.py --screenshots screenshots/objednavka --flow flows/objednavka_main.yaml

# Or with verbose output
python update_flow_coordinates.py -s screenshots/objednavka -f flows/objednavka_main.yaml -v
```

### 2. Run the Updated Flow

```bash
# Execute the main flow with updated coordinates
maestro test flows/objednavka_main.yaml
```

### 3. Manual Coordinate Updates (if needed)

Edit `flows/objednavka_main.yaml` and update the environment variables:

```yaml
env:
  # Login coordinates (already working)
  EMAIL_X: "73"
  EMAIL_Y: "19"
  PASSWORD_X: "73"
  PASSWORD_Y: "25"
  LOGIN_BTN_X: "73"
  LOGIN_BTN_Y: "39"
  
  # Update these with analyzed coordinates
  SEARCH_DOCTOR_X: "45"  # ← Update from analysis
  SEARCH_DOCTOR_Y: "30"  # ← Update from analysis
  
  PATIENT_ID_X: "50"     # ← Update from analysis
  PATIENT_ID_Y: "40"     # ← Update from analysis
  
  NEW_ORDER_X: "60"      # ← Update from analysis
  NEW_ORDER_Y: "50"      # ← Update from analysis
  
  CATEGORY_X: "55"       # ← Update from analysis
  CATEGORY_Y: "70"       # ← Update from analysis
```

## Benefits

✅ **Modular Design**: Each screen/action is in a separate file  
✅ **Parameterized Coordinates**: Easy to update from analysis  
✅ **Reusable Components**: Subflows can be reused across tests  
✅ **Clear Separation**: Analysis phase separate from execution  
✅ **Maintainable**: Changes isolated to specific flows  
✅ **Native Maestro**: Uses built-in runFlow and environment variables  

## Environment Variables

All coordinate variables are defined in `objednavka_main.yaml`:

- `EMAIL_X`, `EMAIL_Y`: Login email field coordinates
- `PASSWORD_X`, `PASSWORD_Y`: Password field coordinates  
- `LOGIN_BTN_X`, `LOGIN_BTN_Y`: Login button coordinates
- `SEARCH_DOCTOR_X`, `SEARCH_DOCTOR_Y`: Doctor search field coordinates
- `PATIENT_ID_X`, `PATIENT_ID_Y`: Patient ID field coordinates
- `NEW_ORDER_X`, `NEW_ORDER_Y`: New order button coordinates
- `CATEGORY_X`, `CATEGORY_Y`: Category selection coordinates

Test data variables:
- `DOCTOR_SEARCH`: Doctor name to search for
- `PATIENT_ID`: Patient identification number

## Troubleshooting

1. **runFlow file not found**: Check that subflow paths are correct relative to the main flow
2. **Environment variables not substituted**: Ensure `${VAR_NAME}` syntax is used correctly
3. **Coordinates still TODO**: Run the coordinate analysis script or manually update values
4. **Flow execution stops**: Check Maestro logs for specific step failures

## Adding New Flows

1. Create new subflow in `subflows/` directory
2. Add environment variables to `objednavka_main.yaml`
3. Add `runFlow` command to main flow
4. Update coordinate analysis mappings in `coordinate_updater.py`