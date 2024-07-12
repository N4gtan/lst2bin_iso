import argparse, shutil, sys
from pathlib import Path
from tqdm import tqdm
from edc_ecc import ComputeEdcBlock, ComputeEccBlock # type: ignore

#[Functions]#####################################################################################################################
def lst_media(file):
	if file.upper().endswith('.LST'):
		lines = Path(file).read_text().upper().splitlines()
		if 'MEDIA=DVD' in lines:
			return 'DVD', lines
		elif 'MEDIA=CD' in lines:
			return 'CD', lines
		else:
			sys.exit(f'Error: File "{INPUT_FILE}" does not have a valid format or is corrupt.')
	return None, None

def lst_files(lines):
	start, end = lines.index('[LST]') + 2, lines.index('[/LST]')
	files = lines[start:end]
	#Check if the files exist and can be opened#
	try:
		for filename in files:
			open(filename,'rb')
	except FileNotFoundError as e:
		sys.exit(e)
	############################################
	return files

def int_to_bcd(i):
    # Converts an integer to BCD (Binary-Coded Decimal)
	return (i // 10 << 4) | (i % 10)

def form1_edc_ecc(subheader, data):
		edc = ComputeEdcBlock(subheader + data, 2056) # form1 subheader + data = 2056 lenght
		ecc_p = ComputeEccBlock(subheader + data + edc, 86, 24, 2, 86)
		ecc_q = ComputeEccBlock(subheader + data + edc + ecc_p, 52, 43, 86, 88)
		return data + edc + ecc_p + ecc_q

def gen_edc_ecc(subheader, data):
	# Check if the sixth bit of the third subheader byte is ON
	if not subheader[2] & 0x20:
		return form1_edc_ecc(subheader, data[:-280])
	data = data[:-4]
	return data + ComputeEdcBlock(subheader + data, 2332) # form2 subheader + data = 2332 lenght

def no_form2_edc(subheader, data):
	if not subheader[2] & 0x20:
		return form1_edc_ecc(subheader, data[:-280])
	return data[:-4] + b'\x00\x00\x00\x00'

def no_edc_ecc(subheader, data):
	if not subheader[2] & 0x20:
		return data[:-280] + b'\x00' * 280
	return data[:-4] + b'\x00\x00\x00\x00'

def no_master(line, size):
	with open(OUTPUT_FILE, 'rb+') as input:
		input.read(line)
		if MEDIA_TYPE == 'DVD':
			input.write(b'\x00' * size * 2)
		else:
			for _ in range(2):
				input.write(CRC(input.read(24)[-8:], b'\x00' * size))

def read_header():
	return input.read(4)

def gen_header():
	read_sector_num = int.from_bytes(sector_num_raw, byteorder='little')
	sector_num = read_sector_num + 150
	remainder = sector_num // 75
	minute_num = int_to_bcd(remainder // 60)
	second_num = int_to_bcd(remainder % 60)
	seventy_fifths_of_a_second_omg_who_thought_this_was_a_good_idea = int_to_bcd(sector_num % 75)
	proprietary_data = input.read(8)
	if proprietary_data != NORMAL_QUASI_HEADER and proprietary_data != NULL_DATA_QUASI_HEADER:
		print(f'Proprietary Sony sector descriptor for sector # {read_sector_num} is 0x{proprietary_data.hex()}, '
			   'which is not currently recognized, and the converted image may be incorrect as a result')
	return bytes([minute_num, second_num, seventy_fifths_of_a_second_omg_who_thought_this_was_a_good_idea]) + b'\x02'
#[/Functions]####################################################################################################################
	
if __name__=='__main__':
	parser = argparse.ArgumentParser(description='This program converts CDVDREC images into normal .bin/iso images',
		epilog='Notes: .000 files are only supported for CD images, .lst is for both DVD and CD images\n'
			   '       .bin/img files are for use with arguments, if no argument is specified defaults to regen EDC/ECC',
		formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('input_file', help=f'supported files .lst/000/bin/img (can drag and drop into {Path(sys.argv[0]).name})')
	parser.add_argument('output_file', nargs='?', help='optional output file path')
	parser.add_argument('-km', '--keepmaster', action='store_true', help='keeps master disc sectors data')
	parser.add_argument('-nf2', '--noform2', action='store_true', help='zeroes form2 EDC and regens form1 EDC/ECC')
	parser.add_argument('-b', '--blank', action='store_true', help='zeroes form1 and form2 EDC/ECC')

	if len(sys.argv) == 1:
		print('Error: the following arguments are required: input_file')
		parser.print_help()
		input("Press Enter key to exit...")
		parser.exit()
	args = parser.parse_args()

	INPUT_FILE = args.input_file
	if not INPUT_FILE.upper().endswith(('.LST', '.000', '.BIN', '.IMG')):
		sys.exit(f'Error: unsuported file type {Path(INPUT_FILE).suffix}')

	#Check if the file exist and can be opened#
	try:
		open(INPUT_FILE,'rb')
	except FileNotFoundError as e:
		sys.exit(e)
	###########################################

	MEDIA_TYPE, LST_LINES = lst_media(INPUT_FILE)
	if MEDIA_TYPE == 'DVD': # input .lst DVD
		OUTPUT_FILE = INPUT_FILE[:-4] + '.iso' if not args.output_file else args.output_file
		files = lst_files(LST_LINES)
		del LST_LINES
		with open(OUTPUT_FILE, 'wb') as output, tqdm(total = len(files)) as pbar:
			for filename in files:
				with open(filename, 'rb') as infile:
					shutil.copyfileobj(infile, output)
				pbar.update(1)
		if not args.keepmaster: # zeroes master disc sectors
			no_master(0x7000, 2048)
		sys.exit()
	elif MEDIA_TYPE == 'CD' or INPUT_FILE[-4:] == '.000': # input .lst CD or .000
		OUTPUT_FILE = INPUT_FILE[:-4] + '.bin' if not args.output_file else args.output_file
		if MEDIA_TYPE: INPUT_FILE = lst_files(LST_LINES)[0]
		del LST_LINES
		SECTOR_SIZE, SYNC_SIZE = 2348, 4
		HEAD = gen_header # generates header (address + mode type) from input
		NORMAL_QUASI_HEADER = b'\x00\x00\x00\x08\x23\x00\x20\x09'
		NULL_DATA_QUASI_HEADER = b'\x04\x00\x00\x08\x23\x00\x20\x09'
	else: # input .bin or .img
		OUTPUT_FILE = INPUT_FILE[:-4] + '_new.bin' if not args.output_file else args.output_file
		SECTOR_SIZE, SYNC_SIZE = 2352, 12
		HEAD = read_header # reads header (address + mode type) from input

	SYNC_BLOCK = b'\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00'
	if not args.blank and not args.noform2: # regens EDC/ECC
		CRC = gen_edc_ecc
	elif args.noform2 and not args.blank: # zeroes form2 EDC and regens form1 EDC/ECC
		CRC = no_form2_edc
	else: CRC = no_edc_ecc # zeroes form1 and form2 EDC/ECC

	with open(INPUT_FILE, 'rb') as input, open(OUTPUT_FILE, 'wb') as output, tqdm(total = Path(INPUT_FILE).stat().st_size // SECTOR_SIZE) as pbar:
		while True:
			sector_num_raw = input.read(SYNC_SIZE)
			if not sector_num_raw:
				break
			header = HEAD()
			subheader = input.read(8)
			data = CRC(subheader, input.read(2328))
			output.write(SYNC_BLOCK + header + subheader + data)
			pbar.update(1)
	if not args.keepmaster: # zeroes master disc sectors
		no_master(0x80A0, 2328)

	if OUTPUT_FILE.upper().endswith('.BIN'):
		with open(OUTPUT_FILE[:-4] + '.cue', 'w') as cue_out:
			cue_out.write(f'FILE "{Path(OUTPUT_FILE).name}" BINARY\n'
				 		   '  TRACK 01 MODE2/2352\n'
						   '    INDEX 01 00:00:00\n')