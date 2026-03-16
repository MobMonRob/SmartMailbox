use std::{
    fs::{self},
    path::{Path, PathBuf},
};

use image::DynamicImage;
use rayon::iter::{IntoParallelRefIterator, ParallelIterator};

#[derive(Debug, Clone, Copy)]
enum BlurStrength {
    Slight,
    Very,
}

impl BlurStrength {
    pub const fn sigma(self) -> f32 {
        match self {
            Self::Slight => 4.5,
            Self::Very => 8.,
        }
    }

    pub const fn label(self) -> &'static str {
        match self {
            Self::Slight => "s",
            Self::Very => "v",
        }
    }
}

fn main() {
    let image_paths: Vec<PathBuf> = fs::read_dir("../server/tests/model/images/")
        .unwrap()
        .map(|p| p.unwrap().path())
        .collect();

    image_paths
        .par_iter()
        .for_each(|path| create_test_images(path));
}

fn create_test_images(path: &Path) {
    let image = image::open(path).unwrap();

    [BlurStrength::Slight, BlurStrength::Very]
        .par_iter()
        .for_each(|blur_strength| blur_image(*blur_strength, &image, path));
}

fn blur_image(blur_strength: BlurStrength, image: &DynamicImage, path: &Path) {
    let blurred_image = image::imageops::blur(image, blur_strength.sigma());

    let file_stem = path.file_stem().unwrap().to_string_lossy();
    let file_stem = file_stem.strip_suffix('p').unwrap();
    let file_extension = path.extension().unwrap().to_string_lossy();

    let file_path = format!("{}{}.{}", file_stem, blur_strength.label(), file_extension);

    let blurred_image_path = path.parent().unwrap().join(file_path);

    blurred_image.save(blurred_image_path).unwrap();
}
