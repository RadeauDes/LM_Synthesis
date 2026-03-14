from opentrons import protocol_api

metadata = {
    'protocolName': 'Workup - Three Plate Transfer (50 µL Pipettes)',
    'author': 'OpentronsAI',
    'description': 'Transfer 400 µL from plate 1 to plate 2, wait 2 minutes, then transfer 400 µL from plate 2 to plate 3 using 50 µL pipettes',
    'source': 'OpentronsAI'
}

requirements = {
    'robotType': 'Flex',
    'apiLevel': '2.25'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load trash bin
    trash = protocol.load_trash_bin('A3')
    
    # Load tip racks - 50 µL filter tips
    # Need 96 tips for first transfer + 96 tips for second transfer = 192 tips total
    tiprack_1 = protocol.load_labware('opentrons_flex_96_filtertiprack_50ul', 'A1', 'Tips for Transfer 1')
    tiprack_2 = protocol.load_labware('opentrons_flex_96_filtertiprack_50ul', 'A2', 'Tips for Transfer 2')
    
    # Load plates
    plate_1 = protocol.load_labware('axygen_96_wellplate_1100ul', 'C1', 'Plate 1 (Source)')
    plate_2 = protocol.load_labware('axygen_96_wellplate_1100ul', 'C2', 'Plate 2 (Intermediate)')
    plate_3 = protocol.load_labware('axygen_96_wellplate_1100ul', 'C3', 'Plate 3 (Final)')
    
    # Load pipettes - 50 µL pipettes
    pipette_1ch = protocol.load_instrument(
        'flex_1channel_50',
        mount='left',
        tip_racks=[tiprack_1, tiprack_2]
    )
    
    pipette_8ch = protocol.load_instrument(
        'flex_8channel_50',
        mount='right',
        tip_racks=[tiprack_1, tiprack_2]
    )
    
    # Define liquids for visualization
    source_liquid = protocol.define_liquid(
        name='Source Solution',
        description='Solution from plate 1',
        display_color='#00FF00'
    )
    
    intermediate_liquid = protocol.define_liquid(
        name='Intermediate Solution',
        description='Solution in plate 2 after acid wash',
        display_color='#FFFF00'
    )
    
    # Load liquids into plates
    for well in plate_1.wells():
        well.load_liquid(liquid=source_liquid, volume=400)
    
    # Transfer 400 µL from plate 1 to plate 2 (column-wise with new tips)
    # Since pipette max is 50 µL, we need 8 cycles of 50 µL to transfer 400 µL
    protocol.comment('Starting transfer from Plate 1 to Plate 2')
    
    for col_index in range(12):  # All 12 columns
        source_col = plate_1.columns()[col_index]
        dest_col = plate_2.columns()[col_index]
        
        protocol.comment(f'Transferring column {col_index + 1} from Plate 1 to Plate 2')
        
        # Pick up new tip for this column
        pipette_8ch.pick_up_tip()
        
        # Transfer 400 µL in 8 cycles of 50 µL each
        for cycle in range(8):
            pipette_8ch.aspirate(50, source_col[0])
            pipette_8ch.dispense(50, dest_col[0])
        
        # Drop tip
        pipette_8ch.drop_tip()
    
    # Wait 2 minutes for acid wash
    protocol.comment('Waiting 2 minutes for acid wash incubation')
    protocol.delay(minutes=2)
    
    # Transfer 400 µL from plate 2 to plate 3 (column-wise with new tips)
    protocol.comment('Starting transfer from Plate 2 to Plate 3')
    
    for col_index in range(12):  # All 12 columns
        source_col = plate_2.columns()[col_index]
        dest_col = plate_3.columns()[col_index]
        
        protocol.comment(f'Transferring column {col_index + 1} from Plate 2 to Plate 3')
        
        # Pick up new tip for this column
        pipette_8ch.pick_up_tip()
        
        # Transfer 400 µL in 8 cycles of 50 µL each
        for cycle in range(8):
            pipette_8ch.aspirate(50, source_col[0])
            pipette_8ch.dispense(50, dest_col[0])
        
        # Drop tip
        pipette_8ch.drop_tip()
    
    protocol.comment('Acid wash workup complete! All transfers finished.')