def find_range(group: str):
    if group.startswith("("):
        index = group.find("-")
        start = group[1:index]
        end = group[index+1:-1]
        return int(start), int(end)+1
    else:
        return int(group), int(group)+1


def gen_ip(ip_groups):
    ips = set()
    for ip_group in ip_groups:
        groups = ip_group.split(".")
        start0, end0 = find_range(groups[0])
        start1, end1 = find_range(groups[1])
        start2, end2 = find_range(groups[2])
        start3, end3 = find_range(groups[3])

        for ip0 in range(start0, end0):
            for ip1 in range(start1, end1):
                for ip2 in range(start2, end2):
                    for ip3 in range(start3, end3):
                        ips.add(f"{ip0}.{ip1}.{ip2}.{ip3}")

    return ips


def gen_firmware(firmwares: list[dict]) -> dict:
    result = {}
    for f in firmwares:
        r_list = result.setdefault(f['sw_type'], [])
        r = {}
        r['version'] = f['version']
        r['file_name'] = f['file_name']
        r['sha256sum'] = f['sha256sum']

        if f['include'] is None:
            r['include'] = {'ALL'}
        else:
            r['include'] = gen_ip(f['include'].split(','))
        
        if f['exclude'] is None:
            r['exclude'] = {}
        else:
            r['exclude'] = gen_ip(f['exclude'].split(','))

        r_list.append(r)

    return result