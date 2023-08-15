import os
import time
from typing import List, Optional
import random


class SaveConfig:
    def __init__(self, **kwargs):
        self.save_every: int = kwargs.get('save_every', 1000)
        self.dtype: str = kwargs.get('save_dtype', 'float16')
        self.max_step_saves_to_keep: int = kwargs.get('max_step_saves_to_keep', 5)


class LogingConfig:
    def __init__(self, **kwargs):
        self.log_every: int = kwargs.get('log_every', 100)
        self.verbose: bool = kwargs.get('verbose', False)
        self.use_wandb: bool = kwargs.get('use_wandb', False)


class SampleConfig:
    def __init__(self, **kwargs):
        self.sample_every: int = kwargs.get('sample_every', 100)
        self.width: int = kwargs.get('width', 512)
        self.height: int = kwargs.get('height', 512)
        self.prompts: list[str] = kwargs.get('prompts', [])
        self.neg = kwargs.get('neg', False)
        self.seed = kwargs.get('seed', 0)
        self.walk_seed = kwargs.get('walk_seed', False)
        self.guidance_scale = kwargs.get('guidance_scale', 7)
        self.sample_steps = kwargs.get('sample_steps', 20)
        self.network_multiplier = kwargs.get('network_multiplier', 1)
        self.guidance_rescale = kwargs.get('guidance_rescale', 0.0)


class NetworkConfig:
    def __init__(self, **kwargs):
        self.type: str = kwargs.get('type', 'lora')
        rank = kwargs.get('rank', None)
        linear = kwargs.get('linear', None)
        if rank is not None:
            self.rank: int = rank  # rank for backward compatibility
            self.linear: int = rank
        elif linear is not None:
            self.rank: int = linear
            self.linear: int = linear
        self.conv: int = kwargs.get('conv', None)
        self.alpha: float = kwargs.get('alpha', 1.0)
        self.linear_alpha: float = kwargs.get('linear_alpha', self.alpha)
        self.conv_alpha: float = kwargs.get('conv_alpha', self.conv)


class TrainConfig:
    def __init__(self, **kwargs):
        self.noise_scheduler = kwargs.get('noise_scheduler', 'ddpm')
        self.steps: int = kwargs.get('steps', 1000)
        self.lr = kwargs.get('lr', 1e-6)
        self.optimizer = kwargs.get('optimizer', 'adamw')
        self.lr_scheduler = kwargs.get('lr_scheduler', 'constant')
        self.max_denoising_steps: int = kwargs.get('max_denoising_steps', 50)
        self.batch_size: int = kwargs.get('batch_size', 1)
        self.dtype: str = kwargs.get('dtype', 'fp32')
        self.xformers = kwargs.get('xformers', False)
        self.train_unet = kwargs.get('train_unet', True)
        self.train_text_encoder = kwargs.get('train_text_encoder', True)
        self.noise_offset = kwargs.get('noise_offset', 0.0)
        self.optimizer_params = kwargs.get('optimizer_params', {})
        self.skip_first_sample = kwargs.get('skip_first_sample', False)
        self.gradient_checkpointing = kwargs.get('gradient_checkpointing', True)


class ModelConfig:
    def __init__(self, **kwargs):
        self.name_or_path: str = kwargs.get('name_or_path', None)
        self.is_v2: bool = kwargs.get('is_v2', False)
        self.is_xl: bool = kwargs.get('is_xl', False)
        self.is_v_pred: bool = kwargs.get('is_v_pred', False)
        self.dtype: str = kwargs.get('dtype', 'float16')
        self.vae_path: str = kwargs.get('vae_path', None)

        if self.name_or_path is None:
            raise ValueError('name_or_path must be specified')


class SliderTargetConfig:
    def __init__(self, **kwargs):
        self.target_class: str = kwargs.get('target_class', '')
        self.positive: str = kwargs.get('positive', '')
        self.negative: str = kwargs.get('negative', '')
        self.multiplier: float = kwargs.get('multiplier', 1.0)
        self.weight: float = kwargs.get('weight', 1.0)


class SliderConfigAnchors:
    def __init__(self, **kwargs):
        self.prompt = kwargs.get('prompt', '')
        self.neg_prompt = kwargs.get('neg_prompt', '')
        self.multiplier = kwargs.get('multiplier', 1.0)


class SliderConfig:
    def __init__(self, **kwargs):
        targets = kwargs.get('targets', [])
        targets = [SliderTargetConfig(**target) for target in targets]
        self.targets: List[SliderTargetConfig] = targets
        anchors = kwargs.get('anchors', [])
        anchors = [SliderConfigAnchors(**anchor) for anchor in anchors]
        self.anchors: List[SliderConfigAnchors] = anchors
        self.resolutions: List[List[int]] = kwargs.get('resolutions', [[512, 512]])
        self.prompt_file: str = kwargs.get('prompt_file', None)
        self.prompt_tensors: str = kwargs.get('prompt_tensors', None)
        self.batch_full_slide: bool = kwargs.get('batch_full_slide', True)


class GenerateImageConfig:
    def __init__(
            self,
            prompt: str = '',
            prompt_2: Optional[str] = None,
            width: int = 512,
            height: int = 512,
            num_inference_steps: int = 50,
            guidance_scale: float = 7.5,
            negative_prompt: str = '',
            negative_prompt_2: Optional[str] = None,
            seed: int = -1,
            network_multiplier: float = 1.0,
            guidance_rescale: float = 0.0,
            # the tag [time] will be replaced with milliseconds since epoch
            output_path: str = None,  # full image path
            output_folder: str = None,  # folder to save image in if output_path is not specified
            output_ext: str = 'png',  # extension to save image as if output_path is not specified
            output_tail: str = '',  # tail to add to output filename
            add_prompt_file: bool = False,  # add a prompt file with generated image
    ):
        self.width: int = width
        self.height: int = height
        self.num_inference_steps: int = num_inference_steps
        self.guidance_scale: float = guidance_scale
        self.guidance_rescale: float = guidance_rescale
        self.prompt: str = prompt
        self.prompt_2: str = prompt_2
        self.negative_prompt: str = negative_prompt
        self.negative_prompt_2: str = negative_prompt_2

        self.output_path: str = output_path
        self.seed: int = seed
        if self.seed == -1:
            # generate random one
            self.seed = random.randint(0, 2 ** 32 - 1)
        self.network_multiplier: float = network_multiplier
        self.output_folder: str = output_folder
        self.output_ext: str = output_ext
        self.add_prompt_file: bool = add_prompt_file
        self.output_tail: str = output_tail
        self.gen_time: int = int(time.time() * 1000)

        # prompt string will override any settings above
        self._process_prompt_string()

        # handle dual text encoder prompts if nothing passed
        if negative_prompt_2 is None:
            self.negative_prompt_2 = negative_prompt

        if prompt_2 is None:
            self.prompt_2 = prompt

        # parse prompt paths
        if self.output_path is None and self.output_folder is None:
            raise ValueError('output_path or output_folder must be specified')
        elif self.output_path is not None:
            self.output_folder = os.path.dirname(self.output_path)
            self.output_ext = os.path.splitext(self.output_path)[1][1:]
            self.output_filename_no_ext = os.path.splitext(os.path.basename(self.output_path))[0]

        else:
            self.output_filename_no_ext = '[time]_[count]'
            if len(self.output_tail) > 0:
                self.output_filename_no_ext += '_' + self.output_tail
            self.output_path = os.path.join(self.output_folder, self.output_filename_no_ext + '.' + self.output_ext)

        # adjust height
        self.height = max(64, self.height - self.height % 8)  # round to divisible by 8
        self.width = max(64, self.width - self.width % 8)  # round to divisible by 8

    def set_gen_time(self, gen_time: int = None):
        if gen_time is not None:
            self.gen_time = gen_time
        else:
            self.gen_time = int(time.time() * 1000)

    def _get_path_no_ext(self, count: int = 0, max_count=0):
        # zero pad count
        count_str = str(count).zfill(len(str(max_count)))
        # replace [time] with gen time
        filename = self.output_filename_no_ext.replace('[time]', str(self.gen_time))
        # replace [count] with count
        filename = filename.replace('[count]', count_str)
        return filename

    def get_image_path(self, count: int = 0, max_count=0):
        filename = self._get_path_no_ext(count, max_count)
        filename += '.' + self.output_ext
        # join with folder
        return os.path.join(self.output_folder, filename)

    def get_prompt_path(self, count: int = 0, max_count=0):
        filename = self._get_path_no_ext(count, max_count)
        filename += '.txt'
        # join with folder
        return os.path.join(self.output_folder, filename)

    def save_image(self, image, count: int = 0, max_count=0):
        # make parent dirs
        os.makedirs(self.output_folder, exist_ok=True)
        self.set_gen_time()
        # TODO save image gen header info for A1111 and us, our seeds probably wont match
        image.save(self.get_image_path(count, max_count))
        # do prompt file
        if self.add_prompt_file:
            self.save_prompt_file(count, max_count)

    def save_prompt_file(self, count: int = 0, max_count=0):
        # save prompt file
        with open(self.get_prompt_path(count, max_count), 'w') as f:
            prompt = self.prompt
            if self.prompt_2 is not None:
                prompt += ' --p2 ' + self.prompt_2
            if self.negative_prompt is not None:
                prompt += ' --n ' + self.negative_prompt
            if self.negative_prompt_2 is not None:
                prompt += ' --n2 ' + self.negative_prompt_2
            prompt += ' --w ' + str(self.width)
            prompt += ' --h ' + str(self.height)
            prompt += ' --seed ' + str(self.seed)
            prompt += ' --cfg ' + str(self.guidance_scale)
            prompt += ' --steps ' + str(self.num_inference_steps)
            prompt += ' --m ' + str(self.network_multiplier)
            prompt += ' --gr ' + str(self.guidance_rescale)

            # get gen info
            f.write(self.prompt)

    def _process_prompt_string(self):
        # we will try to support all sd-scripts where we can

        # FROM SD-SCRIPTS
        # --n Treat everything until the next option as a negative prompt.
        # --w Specify the width of the generated image.
        # --h Specify the height of the generated image.
        # --d Specify the seed for the generated image.
        # --l Specify the CFG scale for the generated image.
        # --s Specify the number of steps during generation.

        # OURS and some QOL additions
        # --m Specify the network multiplier for the generated image.
        # --p2 Prompt for the second text encoder (SDXL only)
        # --n2 Negative prompt for the second text encoder (SDXL only)
        # --gr Specify the guidance rescale for the generated image (SDXL only)

        # --seed Specify the seed for the generated image same as --d
        # --cfg Specify the CFG scale for the generated image same as --l
        # --steps Specify the number of steps during generation same as --s
        # --network_multiplier Specify the network multiplier for the generated image same as --m

        # process prompt string and update values if it has some
        if self.prompt is not None and len(self.prompt) > 0:
            # process prompt string
            prompt = self.prompt
            prompt = prompt.strip()
            p_split = prompt.split('--')
            self.prompt = p_split[0].strip()

            if len(p_split) > 1:
                for split in p_split[1:]:
                    # allows multi char flags
                    flag = split.split(' ')[0].strip()
                    content = split[len(flag):].strip()
                    if flag == 'p2':
                        self.prompt_2 = content
                    elif flag == 'n':
                        self.negative_prompt = content
                    elif flag == 'n2':
                        self.negative_prompt_2 = content
                    elif flag == 'w':
                        self.width = int(content)
                    elif flag == 'h':
                        self.height = int(content)
                    elif flag == 'd':
                        self.seed = int(content)
                    elif flag == 'seed':
                        self.seed = int(content)
                    elif flag == 'l':
                        self.guidance_scale = float(content)
                    elif flag == 'cfg':
                        self.guidance_scale = float(content)
                    elif flag == 's':
                        self.num_inference_steps = int(content)
                    elif flag == 'steps':
                        self.num_inference_steps = int(content)
                    elif flag == 'm':
                        self.network_multiplier = float(content)
                    elif flag == 'network_multiplier':
                        self.network_multiplier = float(content)
                    elif flag == 'gr':
                        self.guidance_rescale = float(content)
