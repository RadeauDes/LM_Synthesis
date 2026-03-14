from opentrons import protocol_api

metadata = {
    'protocolName': 'Amide Coupling Reaction - Multi-Plate Transfer',
    'author': 'OpentronsAI',
    'description': 'Activating agent + carboxylic acid, then amine addition with timed mixing',
    'source': 'OpentronsAI'
}

requirements = {
    'robotType': 'Flex',
    'apiLevel': '2.25'
}

def add_parameters(parameters):
    parameters.add_str(
        variable_name='pipette_1ch_mount',
        display_name='1-Channel Pipette Mount',
        description='Mount position for 1-channel pipette',
        choices=[
            {'display_name': 'Left', 'value': 'left'},
            {'display_name': 'Right', 'value': 'right'}
        ],
        default='left'
    )
    
    parameters.add_str(
        variable_name='pipette_8ch_mount',
        display_name='8-Channel Pipette Mount',
        description='Mount position for 8-channel pipette',
        choices=[
            {'display_name': 'Left', 'value': 'left'},
            {'display_name': 'Right', 'value': 'right'}
        ],
        default='right'
    )

def run(protocol: protocol_api.ProtocolContext):
    # Access runtime parameters
    mount_1ch = protocol.params.pipette_1ch_mount
    mount_8ch = protocol.params.pipette_8ch_mount
    
    # Load trash bin
    trash = protocol.load_trash_bin('A3')
    
    # Load labware - 50 µL filter tip racks for 8-channel pipette
    tiprack_50ul_1 = protocol.load_labware('opentrons_flex_96_filtertiprack_50ul', 'D1')
    tiprack_50ul_2 = protocol.load_labware('opentrons_flex_96_filtertiprack_50ul', 'D2')
    tiprack_50ul_3 = protocol.load_labware('opentrons_flex_96_filtertiprack_50ul', 'D3')
    tiprack_50ul_4 = protocol.load_labware('opentrons_flex_96_filtertiprack_50ul', 'C3')
    
    # Load plates - using custom axygen_96_wellplate_1100ul
    plate_1_activating = protocol.load_labware('axygen_96_wellplate_1100ul', 'C1', 'Activating Agent Plate')
    plate_2_carboxylic = protocol.load_labware('axygen_96_wellplate_1100ul', 'C2', 'Carboxylic Acid Plate')
    plate_3_amine = protocol.load_labware('axygen_96_wellplate_1100ul', 'B1', 'Amine Plate')
    
    # Load pipettes
    pipette_1ch = protocol.load_instrument(
        'flex_1channel_50',
        mount=mount_1ch,
        tip_racks=[tiprack_50ul_1]
    )
    
    pipette_8ch = protocol.load_instrument(
        'flex_8channel_50',
        mount=mount_8ch,
        tip_racks=[tiprack_50ul_1, tiprack_50ul_2, tiprack_50ul_3, tiprack_50ul_4]
    )
    
    # Define liquids
    activating_liquid = protocol.define_liquid(
        name='Activating Agent',
        description='Viscous activating agent for amide coupling',
        display_color='#0000FF'
    )
    
    carboxylic_liquid = protocol.define_liquid(
        name='Carboxylic Acid',
        description='Carboxylic acid substrate',
        display_color='#FF0000'
    )
    
    amine_liquid = protocol.define_liquid(
        name='Amine',
        description='Amine nucleophile',
        display_color='#00FF00'
    )
    
    # Load liquids into labware
    for well in plate_1_activating.columns()[0]:
        well.load_liquid(liquid=activating_liquid, volume=24.8 * 12)  # 24.8 µL × 12 columns
    
    for well in plate_2_carboxylic.wells():
        well.load_liquid(liquid=carboxylic_liquid, volume=50)
    
    for well in plate_3_amine.wells():
        well.load_liquid(liquid=amine_liquid, volume=100)
    
    # Source and destination setup
    activating_source = plate_1_activating.columns()[0]  # Column 1 of Plate 1
    carboxylic_dest_cols = plate_2_carboxylic.columns()[0:12]  # All 12 columns of Plate 2
    amine_source_cols = plate_3_amine.columns()[0:12]  # All 12 columns of Plate 3
    
    # STEP 1: Transfer activating agent to carboxylic acids
    protocol.comment('Step 1: Adding activating agent to carboxylic acids')
    
    # Set flow rates for viscous liquid (5 µL/s)
    pipette_8ch.flow_rate.aspirate = 5
    pipette_8ch.flow_rate.dispense = 5
    
    for dest_col in carboxylic_dest_cols:
        pipette_8ch.pick_up_tip()
        
        # Transfer 24.8 µL
        pipette_8ch.aspirate(24.8, activating_source[0])
        pipette_8ch.dispense(24.8, dest_col[0])
        pipette_8ch.blow_out(dest_col[0])
        
        # Mix 2×40 µL at 10 µL/s
        pipette_8ch.flow_rate.aspirate = 10
        pipette_8ch.flow_rate.dispense = 10
        pipette_8ch.mix(2, 40, dest_col[0])
        
        # Reset flow rates back to 5 µL/s for next transfer
        pipette_8ch.flow_rate.aspirate = 5
        pipette_8ch.flow_rate.dispense = 5
        
        pipette_8ch.drop_tip()
    
    # Wait 5 minutes for activation
    protocol.comment('Waiting 5 minutes for activation')
    protocol.delay(minutes=5)
    
    # STEP 2: Transfer amines to activated carboxylic acids
    protocol.comment('Step 2: Adding amines to activated carboxylic acids')
    
    # Set flow rates for amine transfer (10 µL/s)
    pipette_8ch.flow_rate.aspirate = 10
    pipette_8ch.flow_rate.dispense = 10
    
    for source_col, dest_col in zip(amine_source_cols, carboxylic_dest_cols):
        pipette_8ch.pick_up_tip()
        
        # Transfer 100 µL
        pipette_8ch.aspirate(100, source_col[0])
        pipette_8ch.dispense(100, dest_col[0])
        pipette_8ch.blow_out(dest_col[0])
        
        # Mix 2×40 µL at 10 µL/s (already set)
        pipette_8ch.mix(2, 40, dest_col[0])
        
        pipette_8ch.drop_tip()
    
    protocol.comment('Amide coupling protocol complete!')