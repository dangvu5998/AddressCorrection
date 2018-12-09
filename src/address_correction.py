from collections import defaultdict
from .string_distance import StringDistance

class AddressCorrection:
    '''
    Address correction with phrase compare
    '''
    def __init__(self, cost_dict_path, provinces_path, districts_path, wards_path):
        self.string_distance = StringDistance(cost_dict_path=cost_dict_path)
        self.provinces = []
        self.districts = defaultdict(list)
        self.wards = defaultdict(list)
        with open(provinces_path) as f:
            for line in f:
                entity = line.strip()
                if not entity:
                    break
                self.provinces.append(entity)
        with open(districts_path) as f:
            for line in f:
                entity = line.strip()
                districts, province = entity.split('\t')
                districts = districts.split('|')
                self.districts[province].extend(districts)
        with open(wards_path) as f:
            for line in f:
                entity = line.strip()
                wards, districts, province = entity.split('\t')
                districts = districts.split('|')
                wards = wards.split('|')
                for district in districts:
                    self.wards[(province, district)].extend(wards)

    def provinces_correction(self, phrase, nb_candidates=3):
        '''
        Compare phrase with all provinces
        Return nb_candidate best match provinces
        '''
        if nb_candidates <= 0:
            raise ValueError("Number of candidate must be positive integer")
        
        # store candidate with word and distance pairs
        candidates = [(None, 1000)] * nb_candidates
        for province in self.provinces:
            distance = self.string_distance.distance(phrase, province)
            if distance < candidates[-1][1]:
                candidates[-1] = (province, distance)
                candidates.sort(key=lambda x:x[1])
        return candidates
    
    def correct(self, phrase, correct_phrases, nb_candidates=3, distance_threshold=4):
        candidates = [(None, distance_threshold)] * nb_candidates
        max_diff_length = distance_threshold
        for correct_phrase in correct_phrases:
            if abs(len(phrase) - len(correct_phrase)) >= max_diff_length:
                continue
            distance = self.string_distance.distance(phrase, correct_phrase)
            if distance < candidates[-1][1]:
                candidates[-1] = (correct_phrase, distance)
                candidates.sort(key=lambda x:x[1])
        return candidates

    def _wards_correction(self, tokens, prefix_province, province, prefix_district, district,
                          current_district_index, current_distance, current_result_distance):
        result = None
        result_distance = current_result_distance
        for wards_index in range(max(0, current_district_index - 4), current_district_index):
            phrase = ' '.join(tokens[wards_index:current_district_index])
            correct_walds = self.wards.get((province, district), [])
            wards_candidates = self.correct(phrase, correct_walds)
            for wards, wards_distance in wards_candidates:
                new_distance = current_distance + wards_distance
                if new_distance >= result_distance or wards is None:
                    continue
                def check_prefix():
                    new_wards_index = None
                    prefix_wards = None
                    distance = None
                    if wards_index < 1:
                        return new_wards_index, prefix_wards, distance
                    d = self.string_distance.distance(tokens[wards_index - 1], 'xã')
                    if d < 2:
                        prefix_wards = 'xã'
                        new_wards_index = wards_index - 1
                        distance = d + new_distance
                        return new_wards_index, prefix_wards, distance
                    d = self.string_distance.distance(tokens[wards_index - 1], 'phường')
                    if d < 2:
                        prefix_wards = 'phường'
                        new_wards_index = wards_index - 1
                        distance = d + new_distance
                        return new_wards_index, prefix_wards, distance
                    d = self.string_distance.distance(tokens[wards_index - 1], 'thị trấn')
                    if d <= 2:
                        prefix_wards = 'thị trấn'
                        new_wards_index = wards_index - 1
                        distance = d + new_distance
                        return new_wards_index, prefix_wards, distance
                    if wards_index < 2:
                        return new_wards_index, prefix_wards, distance
                    d = self.string_distance.distance(tokens[wards_index - 2:wards_index], 'thị trấn')
                    if d <= 2:
                        prefix_wards = 'thị trấn'
                        new_wards_index = wards_index - 2
                        distance = d + new_distance
                        return new_wards_index, prefix_wards, distance
                    return new_wards_index, prefix_wards, distance

                new_wards_index, prefix_wards, _ = check_prefix()
                if new_wards_index is None:
                    new_wards_index = wards_index
                wards_normalized = wards + ',' if prefix_wards is None else '{} {},'.format(prefix_wards, wards)
                district_normalized = district + ',' if len(prefix_district) == 0 else \
                    '{} {},'.format(prefix_district, district)
                province_normalized = province if len(prefix_province) == 0 else \
                    '{} {}'.format(prefix_province, province)
                address_composition = [wards_normalized, district_normalized, province_normalized]
                if new_wards_index > 0:
                    prefix_address = ' '.join(tokens[:new_wards_index]) + ','
                    address_composition = [prefix_address] + address_composition
                result = ' '.join(address_composition)
                result_distance = wards_distance + current_distance
        return result, result_distance

    def _district_correction(self, tokens, prefix_province, province,
                             current_province_index, current_distance, current_result_distance):
        result = None
        normalized_province = '{} {}'.format(prefix_province, province) if prefix_province else province
        result_distance = current_result_distance
        for district_index in range(max(0, current_province_index - 4), current_province_index):
            phrase = ' '.join(tokens[district_index:current_province_index])
            correct_districts = self.districts[province]
            district_candidates = self.correct(phrase, correct_districts)
            for district, distance_district in district_candidates:
                new_distance = current_distance + distance_district
                if new_distance >= result_distance or district is None:
                    continue
                if district_index > 0:
                    result_candidate, result_distance_candidate = self._wards_correction(
                        tokens, prefix_province, province, '', district, district_index,
                        new_distance, current_result_distance
                    )
                    if result_distance > result_distance_candidate:
                        result = result_candidate
                        result_distance = result_distance_candidate
                    def check_prefix():
                        new_district_index = None
                        prefix_district = None
                        distance = None
                        if district_index <= 0:
                            return new_district_index, prefix_district, distance
                        d = self.string_distance.distance(tokens[district_index - 1], 'huyện')
                        if d < 2:
                            prefix_district = 'huyện'
                            new_district_index = district_index - 1
                            distance = d + new_distance
                            return new_district_index, prefix_district, distance
                        d = self.string_distance.distance(tokens[district_index - 1], 'tp')
                        if d < 2:
                            prefix_district = 'tp'
                            new_district_index = district_index - 1
                            distance = d + new_distance
                            return new_district_index, prefix_district, distance
                        d = self.string_distance.distance(tokens[district_index - 1], 'thành phố')
                        if d < 2:
                            prefix_district = 'thành phố'
                            new_district_index = district_index - 1
                            distance = d + new_distance
                            return new_district_index, prefix_district, distance
                        if district_index < 2:
                            return new_district_index, prefix_district, distance
                        d = self.string_distance.distance(' '.join(tokens[district_index - 2: district_index]), 'thành phố')
                        if d <= 2:
                            prefix_district = 'thành phố'
                            new_district_index = district_index - 2
                            distance = d + new_distance
                            return new_district_index, prefix_district, distance
                        d = self.string_distance.distance(' '.join(tokens[district_index - 2: district_index]), 'thị xã')
                        if d <= 2:
                            prefix_district = 'thị xã'
                            new_district_index = district_index - 2
                            distance = d + new_distance
                            return new_district_index, prefix_district, distance
                        return new_district_index, prefix_district, distance
                    new_district_index, prefix_district, new_distance = check_prefix()
                    if new_district_index is None:
                        continue
                    if new_district_index > 0:
                        result_candidate, result_distance_candidate = self._wards_correction(
                            tokens, prefix_province, province, prefix_district, district,
                            new_district_index, new_distance, current_result_distance
                        )
                        if result_distance > result_distance_candidate:
                            result = result_candidate
                            result_distance = result_distance_candidate
                    else:
                        if new_distance < result_distance:
                            result_distance = new_distance
                            normalized_district = '{} {}'.format(prefix_district, district)
                            result = '{}, {}'.format(normalized_district, normalized_province)
                elif new_distance < result_distance:
                    result = district + ', ' + normalized_province
                    result_distance = new_distance
        return result, result_distance

    def _province_correction(self, tokens):
        result_distance = 1000
        result = None
        nb_of_tokens = len(tokens)
        for index_province in range(max(0, nb_of_tokens - 4), nb_of_tokens):
            phrase = ' '.join(tokens[index_province:])
            province_candidates = self.correct(phrase, self.provinces)
            for province, distance_province in province_candidates:
                if distance_province > result_distance or province is None:
                    continue
                result_candidate, result_distance_candidate = self._district_correction(
                    tokens, '', province, index_province,
                    distance_province, result_distance
                )
                if result_distance_candidate < result_distance:
                    result_distance = result_distance_candidate
                    result = result_candidate
                if index_province > 0:
                    if self.string_distance.distance(tokens[index_province-1], 'tp') < 2:
                        if index_province <= 1:
                            result = 'tp ' + province
                            result_distance = distance_province
                            continue
                        result_candidate, result_distance_candidate = self._district_correction(
                            tokens, 'tp', province, index_province-1,
                            distance_province, result_distance
                        )
                        if result_distance_candidate < result_distance:
                            result_distance = result_distance_candidate
                            result = result_candidate
                    elif self.string_distance.distance(tokens[index_province-1], 'tỉnh') < 2:
                        if index_province <= 1:
                            result = 'tỉnh ' + province
                            result_distance = distance_province
                            continue
                        result_candidate, result_distance_candidate = self._district_correction(
                            tokens, 'tỉnh', province, index_province-1,
                            distance_province, result_distance
                        )
                        if result_distance_candidate < result_distance:
                            result_distance = result_distance_candidate
                            result = result_candidate
                if index_province <= 0:
                    if distance_province < result_distance:
                        result_distance = distance_province
                        result = province
        return result, result_distance

    def address_correction(self, address):
        '''
        Address should be in format: Ngõ ngách... đường... quận/huyện...tỉnh/thành phố
        and only contain characters
        '''
        tokens = address.split()
        result, distance_result = self._province_correction(tokens)
        return result, distance_result
