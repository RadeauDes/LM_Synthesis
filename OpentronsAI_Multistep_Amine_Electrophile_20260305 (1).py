from opentrons import protocol_api

metadata = {
    'protocolName': 'Amine to Electrophile Transfer - Column-wise',
    'author': 'OpentronsAI',
    'description': 'Transfer 10 µL from plate 1 (amines) to plate 2 (electrophiles) with mixing',
    'source': 'OpentronsAI'
}

requirements = {
    'robotType': 'Flex',
    'apiLevel': '2.25'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load trash bin
    trash = protocol.load_trash_bin('A3')
    
    # Load filter tip racks - 2 boxes for 96 tips (12 columns × 8 tips each)
    tiprack_1 = protocol.load_labware('opentrons_flex_96_filtertiprack_50ul', 'A1', 'Primary Filter Tips')
    tiprack_2 = protocol.load_labware('opentrons_flex_96_filtertiprack_50ul', 'A2', 'Backup Filter Tips')
    
    # Load plates - Axygen 96-well 1100 µL
    plate_1_amine = protocol.load_labware('axygen_96_wellplate_1100ul', 'C1', 'Amine Plate')
    plate_2_electrophile = protocol.load_labware('axygen_96_wellplate_1100ul', 'C2', 'Electrophile Plate')
    
    # Load pipettes
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
    
    # Set flow rates to 5 µL/s for viscous liquids
    pipette_8ch.flow_rate.aspirate = 5
    pipette_8ch.flow_rate.dispense = 5
    
    # Define liquids for visualization
    amine_liquid = protocol.define_liquid(
        name='Amine',
        description='Viscous amine solution',
        display_color='#00FF00'
    )
    
    electrophile_liquid = protocol.define_liquid(
        name='Electrophile',
        description='Electrophile solution',
        display_color='#FF0000'
    )
    
    # Load liquids into plates
    for well in plate_1_amine.wells():
        well.load_liquid(liquid=amine_liquid, volume=500)
    
    for well in plate_2_electrophile.wells():
        well.load_liquid(liquid=electrophile_liquid, volume=25)
    
    # Transfer from each column of plate 1 to corresponding column of plate 2
    protocol.comment('Starting column-wise transfers with mixing')
    
    for col_index in range(12):  # Columns 1-12 (indices 0-11)
        source_col = plate_1_amine.columns()[col_index]
        dest_col = plate_2_electrophile.columns()[col_index]
        
        protocol.comment(f'Transferring column {col_index + 1}')
        
        # Pick up new tip for this column
        pipette_8ch.pick_up_tip()
        
        # Transfer 10 µL
        pipette_8ch.aspirate(25, source_col[0])
        pipette_8ch.dispense(25, dest_col[0])
        
        # Mix 2x with 25 µL
        pipette_8ch.mix(2, 40, dest_col[0])
        
        # Blow out in destination well after mixing
        pipette_8ch.blow_out(dest_col[0])
        
        # Drop tip
        pipette_8ch.drop_tip()
    
    protocol.comment('Protocol complete! All 12 columns transferred and mixed.')