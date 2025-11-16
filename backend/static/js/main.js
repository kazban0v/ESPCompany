(function($) {
    var initialCsrfToken = null;
    var cartState = {
        items: [],
        total_quantity: 0,
        total_amount: '0.00'
    };

    function initFoundation() {
        if (window.Foundation && Foundation.Abide && Foundation.Abide.defaults) {
            Foundation.Abide.defaults.patterns.fio = /^[A-Za-zА-Яа-яЁё\s]+$/;
        }
        if (window.Foundation) {
            // Инициализируем Foundation
            $(document).foundation();

            // Убеждаемся, что все модальные окна инициализированы
            setTimeout(function() {
                $('[data-reveal]').each(function() {
                    var $modal = $(this);
                    try {
                        if (typeof Foundation.getPlugin === 'function') {
                            var plugin = Foundation.getPlugin($modal, 'Reveal');
                            if (!plugin) {
                                new Foundation.Reveal($modal, {
                                    animationIn: 'fade-in',
                                    animationOut: 'fade-out'
                                });
                            }
                        }
                    } catch (err) {
                        console.warn('Error initializing modal:', err);
                    }
                });
            }, 100);
        } else {
            console.warn('Foundation not loaded');
        }
    }

    function initWOW() {
        if (typeof WOW === 'function') {
            new WOW().init();
        }
    }

    function initMasks() {
        if ($.fn.mask) {
            $('.is-phone').mask('+7 (999) 999-99-99');
            // Маски для телефонов в формах
            $('#callback_phone').mask('+7 (999) 999-99-99');
            $('#feedback_phone').mask('+7 (999) 999-99-99');
            $('#consultation_phone').mask('+7 (999) 999-99-99');
        }
    }

    function initSmoothScroll() {
        // Исключаем ссылки категорий из smooth scroll
        $('[data-smooth-scroll]').not('.menu-catalog__items a').off('click.smooth').on('click.smooth', function(event) {
            var href = $(this).attr('href');
            if (!href || href.charAt(0) !== '#') {
                return;
            }
            // Пропускаем ссылки на категории
            if (href.indexOf('#category-') !== -1) {
                return;
            }
            var $target = $(href);
            if ($target.length) {
                var offset = $target.offset();
                if (offset) {
                    event.preventDefault();
                    $('html, body').scrollTop(offset.top - 60);
                }
            }
        });
    }

    function initBenefitsSlider() {
        var $slider = $('.benefits-slider');
        if ($slider.length && $.fn.owlCarousel) {
            $slider.owlCarousel({
                items: 1,
                loop: true,
                margin: 0,
                nav: false,
                dots: true,
                dotsContainer: '#customDots2',
                autoplay: true,
                autoplayTimeout: 5000,
                autoplayHoverPause: true,
                smartSpeed: 600
            });
        }
    }

    function initCanvasClose() {
        $('.canvas-box__close').off('click.canvas').on('click.canvas', function(event) {
            event.preventDefault();
            var $canvas = $(this).closest('.off-canvas');
            if (!$canvas.length) {
                return;
            }
            var plugin = null;
            if (window.Foundation && typeof Foundation.getPlugin === 'function') {
                plugin = Foundation.getPlugin($canvas, 'OffCanvas');
            }
            if (!plugin) {
                plugin = $canvas.data('zfPlugin');
            }
            if (plugin && typeof plugin.close === 'function') {
                plugin.close();
            } else {
                $canvas.removeClass('is-open');
                $('body').removeClass('off-canvas-active');
            }
        });
    }

    function initFancybox() {
        if ($.fn.fancybox) {
            $('[data-fancybox]').fancybox({
                buttons: ['close'],
                loop: false,
                infobar: false
            });
        }
    }

    function getCsrfToken() {
        var match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
        var token = match ? decodeURIComponent(match[1]) : '';
        if (token) {
            initialCsrfToken = token;
        }
        return token || initialCsrfToken || '';
    }

    function renderFormMessage(form, text, isSuccess) {
        var messageEl = form.querySelector('[data-role="form-message"]');
        if (!messageEl) {
            return;
        }

        messageEl.textContent = text || '';
        messageEl.classList.remove('is-success', 'is-error');

        if (text) {
            messageEl.classList.add(isSuccess ? 'is-success' : 'is-error');
            messageEl.style.display = 'block';
        } else {
            messageEl.style.display = 'none';
        }
    }

    function initLeadForms() {
        var $forms = $('.js-lead-form');
        if (!$forms.length) {
            return;
        }

        $forms.each(function() {
            var $form = $(this);
            var formEl = this;
            var leadType = $form.data('lead-type');
            var successText = $form.data('success-text') || 'Спасибо! Ваша заявка отправлена.';
            var token = getCsrfToken();

            if (!leadType) {
                return;
            }

            $form.off('submit.lead').on('submit.lead', function(event) {
                event.preventDefault();
            });

            $form.off('formvalid.zf.abide.lead').on('formvalid.zf.abide.lead', function(event) {
                event.preventDefault();
                if ($form.hasClass('is-loading')) {
                    return;
                }

                $form.addClass('is-loading');
                renderFormMessage(formEl, '', true);

                var formData = new FormData(formEl);
                var payload = {
                    lead_type: leadType,
                    name: (formData.get('NAME') || '').trim(),
                    email: (formData.get('EMAIL') || '').trim(),
                    phone: (formData.get('PHONE') || '').trim(),
                    message: (formData.get('MESSAGE') || '').trim(),
                };

                fetch('/api/leads/', {
                        method: 'POST',
                        credentials: 'same-origin',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': token,
                        },
                        body: JSON.stringify(payload),
                    })
                    .then(function(response) {
                        if (!response.ok) {
                            return response.json().catch(function() {
                                return {
                                    success: false,
                                    message: 'Не удалось отправить форму.'
                                };
                            }).then(function(data) {
                                throw data;
                            });
                        }
                        return response.json();
                    })
                    .then(function(data) {
                        renderFormMessage(formEl, data.message || successText, true);
                        formEl.reset();
                        $form.removeClass('is-loading');
                    })
                    .catch(function(error) {
                        var message = 'Не удалось отправить форму. Попробуйте позже.';
                        if (error && error.message) {
                            message = error.message;
                        }
                        renderFormMessage(formEl, message, false);
                        $form.removeClass('is-loading');
                    });
            });
        });
    }

    function initFaq() {
        var $items = $('.faq-box');
        if (!$items.length) {
            return;
        }

        $items.find('.faq-box__body').hide();

        $items.each(function() {
            var $item = $(this);
            var $head = $item.find('.faq-box__head');
            var $body = $item.find('.faq-box__body');

            $head.off('click.faq').on('click.faq', function() {
                if ($body.is(':visible')) {
                    $body.slideUp(200);
                    $item.removeClass('is-open');
                } else {
                    $items.removeClass('is-open').find('.faq-box__body:visible').slideUp(200);
                    $body.slideDown(200);
                    $item.addClass('is-open');
                }
            });
        });
    }

    function initCatalogMenu() {
        var $containers = $('.menu-catalog, #offCanvasRightMenu');
        if (!$containers.length) {
            return;
        }

        var selector = '.menu-catalog__items .has-dropdown';
        var submenuSelector = '> .menu-catalog__items';

        // hide all submenus initially
        $containers.find(selector + ' ' + submenuSelector).hide();

        // open items marked active by default
        $containers.find(selector).each(function() {
            var $item = $(this);
            var $link = $item.children('a');
            if ($link.hasClass('active')) {
                $item.addClass('is-open');
                $item.children('ul.menu-catalog__items').show();
            }
        });

        // Обработка кликов на категории в меню
        $(document).off('click.categoryMenuToggle', '.category-menu-toggle').on('click.categoryMenuToggle', '.category-menu-toggle', function(event) {
            var $link = $(this);
            var categoryId = $link.data('category-id');

            if (!categoryId) {
                return;
            }

            event.preventDefault();
            event.stopPropagation();

            // Открываем/закрываем подменю в меню
            var $parent = $link.parent('li');
            var $submenu = $parent.children('ul.menu-catalog__items');

            if ($parent.hasClass('is-open')) {
                $parent.removeClass('is-open');
                $submenu.hide();
            } else {
                var $siblings = $parent.siblings('.has-dropdown');
                $siblings.removeClass('is-open').children('ul.menu-catalog__items').hide();
                $parent.addClass('is-open');
                $submenu.show();
            }

            // Кликаем на соответствующую категорию в контенте
            var $contentToggle = $('.category-toggle[data-category-id="' + categoryId + '"]');
            if ($contentToggle.length) {
                $contentToggle.trigger('click');
            }

            // Прокручиваем к каталогу
            var $catalogSection = $('#catalog');
            if ($catalogSection.length) {
                var offset = $catalogSection.offset();
                if (offset) {
                    $('html, body').scrollTop(offset.top - 60);
                }
            }
        });

        // Обработка кликов на подкатегории в меню
        $(document).off('click.subcategoryMenuToggle', '.subcategory-menu-toggle').on('click.subcategoryMenuToggle', '.subcategory-menu-toggle', function(event) {
            var $link = $(this);
            var subcategoryId = $link.data('subcategory-id');

            if (!subcategoryId) {
                return;
            }

            event.preventDefault();
            event.stopPropagation();

            // Открываем/закрываем подменю в меню
            var $parent = $link.parent('li');
            var $submenu = $parent.children('ul.menu-catalog__items');

            if ($parent.hasClass('is-open')) {
                $parent.removeClass('is-open');
                $submenu.hide();
                // Убеждаемся, что ссылка подкатегории видна
                $link.css('display', '').show();
            } else {
                var $siblings = $parent.siblings('.has-dropdown');
                $siblings.removeClass('is-open').children('ul.menu-catalog__items').hide();
                $parent.addClass('is-open');
                $submenu.show();
                // Убеждаемся, что ссылка подкатегории видна при открытии разделов
                $link.css('display', '').show();
            }

            // Кликаем на соответствующую подкатегорию в контенте
            var $contentToggle = $('.subcategory-toggle[data-subcategory-id="' + subcategoryId + '"]');
            if ($contentToggle.length) {
                $contentToggle.trigger('click');
            }

            // Прокручиваем к каталогу
            var $catalogSection = $('#catalog');
            if ($catalogSection.length) {
                var offset = $catalogSection.offset();
                if (offset) {
                    $('html, body').scrollTop(offset.top - 60);
                }
            }
        });

        // Обработка кликов на разделы (Section) в меню
        $(document).off('click.sectionMenuToggle', '.section-menu-toggle').on('click.sectionMenuToggle', '.section-menu-toggle', function(event) {
            var $link = $(this);
            var sectionId = $link.data('section-id');

            if (!sectionId) {
                return;
            }

            event.preventDefault();
            event.stopPropagation();

            // Убираем активный класс со всех ссылок
            $('.menu-catalog__items a').removeClass('active');
            // Добавляем активный класс к текущей ссылке
            $link.addClass('active');

            // Показываем контейнер товаров
            var $mainContainer = $('#products-container');
            if ($mainContainer.length) {
                $mainContainer.show();
            }

            // Кликаем на соответствующий раздел в контенте
            var $contentToggle = $('.section-toggle[data-section-id="' + sectionId + '"]');
            if ($contentToggle.length) {
                $contentToggle.trigger('click');
            } else {
                // Если раздел не найден в скрытой структуре, показываем товары напрямую
                if ($mainContainer.length) {
                    $mainContainer.find('.product-item').hide();
                    $mainContainer.find('.product-item[data-section-id="' + sectionId + '"]').show();
                }
            }

            // Прокручиваем к каталогу
            var $catalogSection = $('#catalog');
            if ($catalogSection.length) {
                var offset = $catalogSection.offset();
                if (offset) {
                    $('html, body').scrollTop(offset.top - 60);
                }
            }
        });


    }

    // Хранилище открытых категорий для предотвращения бесконечной рекурсии
    var openedCategories = {};

    function openCategory(categoryId, depth) {
        // Защита от бесконечной рекурсии
        depth = depth || 0;
        if (depth > 10) {
            return;
        }

        // Если категория уже открыта на этом уровне, пропускаем
        if (openedCategories[categoryId] && openedCategories[categoryId] >= depth) {
            return;
        }
        openedCategories[categoryId] = depth;

        var $section = $('#category-' + categoryId);
        if (!$section.length) {
            console.log('Секция не найдена:', categoryId);
            return;
        }

        console.log('Открытие категории:', categoryId);

        // Открываем все родительские секции
        var $parentSection = $section.parent().closest('.catalog-section');
        while ($parentSection.length && $parentSection.attr('id')) {
            var parentId = parseInt($parentSection.attr('id').replace('category-', ''), 10);
            if (parentId && !openedCategories[parentId]) {
                if ($parentSection.is(':hidden')) {
                    $parentSection.show();
                }
                openedCategories[parentId] = depth - 1;
            }
            $parentSection = $parentSection.parent().closest('.catalog-section');
        }

        // Показываем секцию категории
        if ($section.is(':hidden')) {
            $section.show();
        }

        var $toggle = $('.category-toggle[data-category-id="' + categoryId + '"]');
        var $products = $('.category-products[data-category-id="' + categoryId + '"]');

        console.log('Toggle:', $toggle.length, 'Products:', $products.length);

        // Открываем товары
        if ($products.length) {
            $toggle.addClass('is-open');
            // ИСПРАВЛЕНИЕ: принудительно показываем товары
            $products.css('display', 'flex').show();
            console.log('Товары открыты для категории:', categoryId);
        }

        // Открываем все дочерние категории
        var $childSections = $section.find('.catalog-section');
        console.log('Найдено дочерних секций:', $childSections.length);

        $childSections.each(function() {
            var $childSection = $(this);
            var childIdMatch = $childSection.attr('id');

            if (childIdMatch && childIdMatch.indexOf('category-') === 0) {
                var childCategoryId = parseInt(childIdMatch.replace('category-', ''), 10);

                if (childCategoryId && childCategoryId !== categoryId && !openedCategories[childCategoryId]) {
                    console.log('Обработка дочерней категории:', childCategoryId);

                    // Показываем дочернюю секцию
                    if ($childSection.is(':hidden')) {
                        $childSection.show();
                    }

                    // Открываем товары в дочерней категории
                    var $childProducts = $('.category-products[data-category-id="' + childCategoryId + '"]');
                    if ($childProducts.length) {
                        var $childToggle = $('.category-toggle[data-category-id="' + childCategoryId + '"]');
                        $childToggle.addClass('is-open');
                        // ИСПРАВЛЕНИЕ: принудительно показываем товары
                        $childProducts.css('display', 'flex').show();
                        console.log('Товары открыты для дочерней категории:', childCategoryId);
                    }

                    // Рекурсивно открываем вложенные категории
                    openCategory(childCategoryId, depth + 1);
                }
            }
        });
    }

    function filterProductsByCategory(categoryId) {
        // Если categoryId = 0, показываем все товары
        if (!categoryId || categoryId === 0) {
            $('.product-item').show();
            $('#load-more-products').hide();
            updateProductsCount();
            return;
        }

        // Скрываем все товары
        $('.product-item').hide();

        // Показываем товары из выбранной категории и всех её подкатегорий
        var categoryIds = [categoryId];

        // Находим все дочерние категории
        function findChildCategories(parentId) {
            var $menuLink = $('.menu-catalog__items a[href="#category-' + parentId + '"]');
            if ($menuLink.length) {
                var $parent = $menuLink.parent('.has-dropdown');
                if ($parent.length) {
                    $parent.find('.menu-catalog__items a').each(function() {
                        var href = $(this).attr('href');
                        var match = href ? href.match(/#category-(\d+)/) : null;
                        if (match && match[1]) {
                            var childId = parseInt(match[1], 10);
                            if (categoryIds.indexOf(childId) === -1) {
                                categoryIds.push(childId);
                                findChildCategories(childId);
                            }
                        }
                    });
                }
            }
        }

        findChildCategories(categoryId);

        // Показываем товары из всех найденных категорий (первые 24)
        var shownCount = 0;
        categoryIds.forEach(function(catId) {
            $('.product-item[data-category-id="' + catId + '"]').each(function() {
                if (shownCount < 24) {
                    $(this).show();
                    shownCount++;
                }
            });
        });

        // Если не нашли товары по data-category-id, используем альтернативный метод
        if ($('.product-item[data-category-id]').length === 0) {
            // Показываем все товары, так как фильтрация по data-category-id не работает
            $('.product-item').slice(0, 24).show();
        }

        // Скрываем кнопку "Показать еще" при фильтрации
        $('#load-more-products').hide();

        updateProductsCount();
    }

    function initCategoryToggle() {
        // Обработка кликов на категории - показывает подкатегории
        $(document).off('click.categoryToggle', '.category-toggle').on('click.categoryToggle', '.category-toggle', function(event) {
            event.preventDefault();
            event.stopPropagation();

            var $toggle = $(this);
            var categoryId = $toggle.data('category-id');
            if (!categoryId) {
                return;
            }

            var $subcategories = $('.category-subcategories[data-category-id="' + categoryId + '"]');
            if (!$subcategories.length) {
                return;
            }

            var isOpen = $toggle.hasClass('is-open');

            if (isOpen) {
                // Закрываем категорию - скрываем подкатегории
                $toggle.removeClass('is-open');
                $subcategories.hide();
            } else {
                // Закрываем все другие категории
                $('.category-toggle.is-open').each(function() {
                    var $otherToggle = $(this);
                    var otherCategoryId = $otherToggle.data('category-id');
                    $otherToggle.removeClass('is-open');
                    $('.category-subcategories[data-category-id="' + otherCategoryId + '"]').hide();
                });

                // Открываем текущую категорию - показываем подкатегории
                $toggle.addClass('is-open');
                $subcategories.show();
            }
        });

        // Обработка кликов на подкатегории - показывает разделы
        $(document).off('click.subcategoryToggle', '.subcategory-toggle').on('click.subcategoryToggle', '.subcategory-toggle', function(event) {
            event.preventDefault();
            event.stopPropagation();

            var $toggle = $(this);
            var subcategoryId = $toggle.data('subcategory-id');
            if (!subcategoryId) {
                return;
            }

            var $sections = $('.subcategory-sections[data-subcategory-id="' + subcategoryId + '"]');
            if (!$sections.length) {
                return;
            }

            var isOpen = $toggle.hasClass('is-open');

            // Находим контейнер подкатегории и описание
            var $subcategoryContainer = $toggle.closest('.catalog-subsection');
            var $subcategoryDescription = $subcategoryContainer.find('.catalog-description');

            if (isOpen) {
                // Закрываем подкатегорию - скрываем разделы
                $toggle.removeClass('is-open');
                $sections.hide();
                // Убеждаемся, что описание видно
                if ($subcategoryDescription.length) {
                    $subcategoryDescription.show();
                }
            } else {
                // Закрываем все другие подкатегории в этой категории
                var $parentCategory = $toggle.closest('.category-subcategories');
                var categoryId = $parentCategory.data('category-id');
                $parentCategory.find('.subcategory-toggle.is-open').each(function() {
                    var $otherToggle = $(this);
                    var otherSubcategoryId = $otherToggle.data('subcategory-id');
                    $otherToggle.removeClass('is-open');
                    $('.subcategory-sections[data-subcategory-id="' + otherSubcategoryId + '"]').hide();
                });

                // Открываем текущую подкатегорию - показываем разделы
                $toggle.addClass('is-open');
                $sections.show();
                // Убеждаемся, что описание подкатегории видно
                if ($subcategoryDescription.length) {
                    $subcategoryDescription.show();
                }
            }
        });

        // Обработчик кнопки "Показать еще" для загрузки дополнительных товаров
        $(document).off('click.loadMore', '.section-load-more-btn').on('click.loadMore', '.section-load-more-btn', function(event) {
            event.preventDefault();
            event.stopPropagation();

            var $btn = $(this);
            var sectionId = $btn.data('section-id');
            var offset = parseInt($btn.data('offset')) || 9;
            var limit = parseInt($btn.data('limit')) || 9;

            if (!sectionId) {
                return;
            }

            // Блокируем кнопку во время загрузки
            $btn.prop('disabled', true).text('Загрузка...');

            // Загружаем товары через AJAX
            $.ajax({
                url: '/api/section/products/',
                method: 'GET',
                data: {
                    section_id: sectionId,
                    offset: offset,
                    limit: limit
                },
                success: function(response) {
                    if (response.success && response.html) {
                        // Находим контейнер товаров
                        var $mainContainer = $('#products-container');
                        var $hiddenProductsContainer = $('.section-products[data-section-id="' + sectionId + '"]');

                        if ($mainContainer.length) {
                            // Добавляем товары в основной контейнер
                            var $newProducts = $(response.html);
                            $newProducts.each(function() {
                                var $productBox = $(this).find('.product-box');
                                var productSku = $productBox.data('product');
                                if (productSku) {
                                    // Ищем существующий элемент по SKU
                                    var $existing = $mainContainer.find('.product-item[data-product="' + productSku + '"]');
                                    if ($existing.length) {
                                        // Показываем существующий товар
                                        $existing.show();
                                    } else {
                                        // Создаем новый элемент из шаблона
                                        var $productItem = $('<div class="column column-block product-item" data-product="' + productSku + '" data-section-id="' + sectionId + '"></div>');
                                        $productItem.html($(this).html());
                                        $mainContainer.append($productItem);
                                    }
                                }
                            });

                            // Обновляем счетчик товаров
                            if (typeof updateProductsCount === 'function') {
                                updateProductsCount();
                            }
                        } else if ($hiddenProductsContainer.length) {
                            // Добавляем товары в скрытый контейнер (если основной контейнер не найден)
                            $hiddenProductsContainer.append(response.html);

                            // Показываем скрытый контейнер, если он был скрыт
                            $hiddenProductsContainer.css({
                                'visibility': 'visible',
                                'position': 'static',
                                'left': 'auto',
                                'width': 'auto',
                                'height': 'auto',
                                'overflow': 'visible',
                                'display': 'flex'
                            });
                        }

                        // Обновляем offset для следующей загрузки
                        var newOffset = offset + limit;
                        $btn.data('offset', newOffset);

                        // Если больше нет товаров, скрываем кнопку
                        if (!response.has_more) {
                            $btn.hide();
                            var $loadMoreContainer = $('#load-more-container');
                            if ($loadMoreContainer.length) {
                                $loadMoreContainer.hide();
                            }
                        } else {
                            $btn.prop('disabled', false).text('Показать еще');
                        }
                    } else {
                        $btn.prop('disabled', false).text('Показать еще');
                        console.error('Ошибка загрузки товаров:', response.message || 'Неизвестная ошибка');
                    }
                },
                error: function(xhr, status, error) {
                    $btn.prop('disabled', false).text('Показать еще');
                    console.error('Ошибка AJAX:', error);
                }
            });
        });

        // Обработчик кликов по разделам (Section) - показывает товары в основном контейнере
        $(document).off('click.sectionToggle', '.section-toggle').on('click.sectionToggle', '.section-toggle', function(event) {
            event.preventDefault();
            event.stopPropagation();

            var $toggle = $(this);
            var sectionId = $toggle.data('section-id');
            if (!sectionId) {
                return;
            }

            // Находим товары из скрытой структуры
            var $hiddenProducts = $('.section-products[data-section-id="' + sectionId + '"] .product-box');
            var $mainContainer = $('#products-container');
            var $hiddenProductsContainer = $('.section-products[data-section-id="' + sectionId + '"]');

            var isOpen = $toggle.hasClass('is-open');

            if (isOpen) {
                // Закрываем раздел - скрываем товары и показываем структуру категорий обратно
                $toggle.removeClass('is-open');

                // Убираем класс с body
                $('body').removeClass('section-products-open');

                if ($mainContainer.length) {
                    $mainContainer.hide();
                }
                if ($hiddenProductsContainer.length) {
                    $hiddenProductsContainer.hide();
                }

                // Показываем структуру категорий обратно
                $('.catalog-section').show();
                $('.catalog-section__header').show();
                $('.catalog-subsection').show();
                $('.catalog-subsection__title').show();
                $('.catalog-section-item').show();
                $('.catalog-section-item__title').show();

                // Скрываем кнопку "Показать еще"
                var $loadMoreBtn = $('#load-more-btn');
                var $loadMoreContainer = $('#load-more-container');
                if ($loadMoreBtn.length) {
                    $loadMoreBtn.hide();
                }
                if ($loadMoreContainer.length) {
                    $loadMoreContainer.hide();
                }
            } else {
                // Закрываем все другие разделы в этой подкатегории
                var $parentSubcategory = $toggle.closest('.subcategory-sections');
                if ($parentSubcategory.length) {
                    var subcategoryId = $parentSubcategory.data('subcategory-id');
                    $parentSubcategory.find('.section-toggle.is-open').each(function() {
                        var $otherToggle = $(this);
                        var otherSectionId = $otherToggle.data('section-id');
                        $otherToggle.removeClass('is-open');
                        $('.section-products[data-section-id="' + otherSectionId + '"]').hide();
                    });
                }

                // Открываем текущий раздел - показываем товары
                $toggle.addClass('is-open');

                // Добавляем класс к body для скрытия заголовков
                $('body').addClass('section-products-open');

                // Скрываем ВСЕ элементы структуры категорий/подкатегорий/разделов справа
                // Используем более агрессивный подход - скрываем все элементы структуры категорий

                // 1. Скрываем все элементы структуры категорий глобально
                $('.catalog-section').hide().css('display', 'none');
                $('.catalog-section__header').hide().css('display', 'none');
                $('.catalog-subsection').hide().css('display', 'none');
                $('.catalog-subsection__title').hide().css('display', 'none');
                $('.catalog-section-item').hide().css('display', 'none');
                $('.catalog-section-item__title').hide().css('display', 'none');
                $('.category-subcategories').hide().css('display', 'none');
                $('.subcategory-sections').hide().css('display', 'none');

                // 2. Скрываем элементы внутри контейнера каталога
                $('#catalog .catalog-section').hide().css('display', 'none');
                $('#catalog .catalog-section__header').hide().css('display', 'none');
                $('#catalog .catalog-subsection').hide().css('display', 'none');
                $('#catalog .catalog-subsection__title').hide().css('display', 'none');
                $('#catalog .catalog-section-item').hide().css('display', 'none');
                $('#catalog .catalog-section-item__title').hide().css('display', 'none');
                $('#catalog .category-subcategories').hide().css('display', 'none');
                $('#catalog .subcategory-sections').hide().css('display', 'none');

                // 3. Скрываем элементы внутри .catalog-box
                $('.catalog-box .catalog-section').hide().css('display', 'none');
                $('.catalog-box .catalog-section__header').hide().css('display', 'none');
                $('.catalog-box .catalog-subsection').hide().css('display', 'none');
                $('.catalog-box .catalog-subsection__title').hide().css('display', 'none');
                $('.catalog-box .catalog-section-item').hide().css('display', 'none');
                $('.catalog-box .catalog-section-item__title').hide().css('display', 'none');
                $('.catalog-box .category-subcategories').hide().css('display', 'none');
                $('.catalog-box .subcategory-sections').hide().css('display', 'none');

                // 4. Скрываем скрытую структуру категорий (она уже скрыта, но убеждаемся)
                $('[style*="visibility: hidden"]').each(function() {
                    $(this).css({
                        'visibility': 'hidden',
                        'position': 'absolute',
                        'left': '-9999px',
                        'width': '1px',
                        'height': '1px',
                        'overflow': 'hidden',
                        'display': 'none'
                    });
                });

                // Показываем контейнер товаров
                if ($mainContainer.length) {
                    $mainContainer.show();

                    // Показываем контейнер для кнопки "Показать еще"
                    var $loadMoreContainer = $('#load-more-container');
                    if ($loadMoreContainer.length) {
                        $loadMoreContainer.show();
                    }

                    // Скрываем все товары
                    $mainContainer.find('.product-item').hide();

                    // Показываем только товары из этого раздела (первые 9)
                    var foundProducts = 0;
                    var shownCount = 0;
                    var maxShow = 9; // Показываем только первые 9 товаров

                    if ($hiddenProducts.length) {
                        // Используем товары из скрытой структуры по SKU
                        $hiddenProducts.each(function() {
                            if (shownCount >= maxShow) {
                                return false; // Прерываем цикл после 9 товаров
                            }
                            var productSku = $(this).data('product');
                            if (productSku) {
                                var $productItem = $mainContainer.find('.product-item[data-product="' + productSku + '"]');
                                if ($productItem.length) {
                                    $productItem.show();
                                    // Принудительно загружаем изображения
                                    $productItem.find('img').each(function() {
                                        var $img = $(this);
                                        if ($img.attr('src') && !$img.data('loaded')) {
                                            var img = new Image();
                                            img.src = $img.attr('src');
                                            $img.data('loaded', true);
                                        }
                                    });
                                    foundProducts++;
                                    shownCount++;
                                }
                            }
                        });
                    }

                    // Проверяем, нужно ли показывать кнопку "Показать еще"
                    // Считаем товары в разделе из основного контейнера
                    var totalProductsInSection = $mainContainer.find('.product-item[data-section-id="' + sectionId + '"]').length;
                    if (totalProductsInSection === 0) {
                        // Если товары не найдены по data-section-id, считаем по SKU из скрытого контейнера
                        totalProductsInSection = $hiddenProducts.length;
                    }

                    // Показываем кнопку "Показать еще", если товаров больше 9
                    var $loadMoreBtn = $('#load-more-btn');
                    var $loadMoreContainer = $('#load-more-container');
                    if (totalProductsInSection > maxShow && $loadMoreBtn.length) {
                        $loadMoreBtn.attr('data-section-id', sectionId).data('section-id', sectionId).data('offset', maxShow).data('limit', 9).show();
                        if ($loadMoreContainer.length) {
                            $loadMoreContainer.show();
                        }
                    } else {
                        $loadMoreBtn.hide();
                        if ($loadMoreContainer.length) {
                            $loadMoreContainer.hide();
                        }
                    }

                    // Если товары не найдены по SKU, используем data-section-id
                    if (foundProducts === 0) {
                        var $sectionProducts = $mainContainer.find('.product-item[data-section-id="' + sectionId + '"]');
                        var totalInSection = $sectionProducts.length;
                        if ($sectionProducts.length) {
                            // Показываем только первые 9 товаров
                            $sectionProducts.slice(0, maxShow).show();
                            // Принудительно загружаем изображения
                            $sectionProducts.slice(0, maxShow).find('img').each(function() {
                                var $img = $(this);
                                if ($img.attr('src') && !$img.data('loaded')) {
                                    var img = new Image();
                                    img.src = $img.attr('src');
                                    $img.data('loaded', true);
                                }
                            });
                            foundProducts = Math.min(maxShow, totalInSection);

                            // Показываем кнопку "Показать еще", если товаров больше 9
                            var $loadMoreBtn = $('#load-more-btn');
                            var $loadMoreContainer = $('#load-more-container');
                            if (totalInSection > maxShow && $loadMoreBtn.length) {
                                $loadMoreBtn.data('section-id', sectionId).data('offset', maxShow).data('limit', 9).show();
                                if ($loadMoreContainer.length) {
                                    $loadMoreContainer.show();
                                }
                            } else {
                                $loadMoreBtn.hide();
                            }
                        }
                    }

                    // Если товары все еще не найдены, показываем товары из скрытой структуры напрямую
                    if (foundProducts === 0 && $hiddenProductsContainer.length) {
                        // Показываем товары из скрытой структуры напрямую
                        $hiddenProductsContainer.css({
                            'visibility': 'visible',
                            'position': 'static',
                            'left': 'auto',
                            'width': 'auto',
                            'height': 'auto',
                            'overflow': 'visible',
                            'display': 'flex'
                        }).show();

                        // Показываем кнопку "Показать еще" рядом с контейнером товаров
                        var $loadMoreBtn = $('.section-load-more[data-section-id="' + sectionId + '"]');
                        if ($loadMoreBtn.length) {
                            $loadMoreBtn.insertAfter($hiddenProductsContainer).show();
                        }

                        // Принудительно загружаем изображения из скрытой структуры
                        $hiddenProductsContainer.find('img').each(function() {
                            var $img = $(this);
                            if ($img.attr('src') && !$img.data('loaded')) {
                                var img = new Image();
                                img.onload = function() {
                                    $img.attr('src', img.src);
                                };
                                img.src = $img.attr('src');
                                $img.data('loaded', true);
                            }
                        });

                        // Также пытаемся найти товары в основном контейнере по SKU
                        $hiddenProductsContainer.find('.product-box').each(function() {
                            var $productBox = $(this);
                            var productSku = $productBox.data('product');
                            if (productSku) {
                                var $existingProduct = $mainContainer.find('.product-item[data-product="' + productSku + '"]');
                                if ($existingProduct.length) {
                                    $existingProduct.show();
                                    // Принудительно загружаем изображения
                                    $existingProduct.find('img').each(function() {
                                        var $img = $(this);
                                        if ($img.attr('src') && !$img.data('loaded')) {
                                            var img = new Image();
                                            img.src = $img.attr('src');
                                            $img.data('loaded', true);
                                        }
                                    });
                                    foundProducts++;
                                }
                            }
                        });

                        // Если нашли товары в основном контейнере, скрываем скрытую структуру
                        if (foundProducts > 0) {
                            $hiddenProductsContainer.hide();
                        }
                    }
                } else if ($hiddenProductsContainer.length) {
                    // Если нет основного контейнера, показываем товары из скрытой структуры напрямую
                    $hiddenProductsContainer.css('display', 'flex').show();
                }
            }
        });

    }

    function formatPrice(value) {
        var number = parseFloat(normalizePrice(value));
        if (isNaN(number)) {
            number = 0;
        }
        return new Intl.NumberFormat('ru-RU').format(number);
    }

    function normalizePrice(value) {
        if (typeof value === 'number') {
            return value.toString();
        }
        if (!value) {
            return '0';
        }
        return value.toString().replace(/\s/g, '').replace('\xa0', '').replace(',', '.');
    }

    function extractProductData($btn) {
        var data = $btn.data();
        var productId = data.productId || data.id;
        var $productBox = $btn.closest('.product-box');
        var title = data.title;
        var sku = data.sku;
        var price = data.price;

        if ($productBox.length) {
            if (!title) {
                // Ищем title в правильном порядке: сначала в самом product-box
                title = $productBox.find('.product-box__title').first().text().trim() ||
                    $productBox.find('.product-box__photo img').attr('alt') ||
                    '';
            }
            if (!sku) {
                var skuText = $productBox.find('.product-box__sku').text();
                if (skuText) {
                    sku = skuText.replace('Маркировка:', '').trim();
                }
            }
            if (!price) {
                price = $productBox.find('.product-box__price-value')
                    .first()
                    .text()
                    .replace(/[^\d.,]/g, '');
            }
        }

        if (title) {
            $btn.data('title', title);
        }
        if (sku) {
            $btn.data('sku', sku);
        }
        if (price) {
            $btn.data('price', price);
        }

        return {
            productId: productId,
            title: title,
            sku: sku || '',
            price: normalizePrice(price)
        };
    }

    function updateCartCounters(state) {
        var count = state.total_quantity || 0;
        var amount = state.total_amount || '0.00';
        $('.dev_count_cart').text(count);
        $('.dev_price_cart').text(formatPrice(amount));
    }

    function renderCartModal(state) {
        var container = document.getElementById('dev_cart_ajax');
        if (!container) {
            return;
        }

        if (!state.items.length) {
            container.innerHTML = '<div class="box-modal__title"><i class="icon-basket"></i>Корзина пуста</div>' +
                '<p class="cart-empty-text">Добавьте товары из каталога, чтобы оформить заказ.</p>';
            return;
        }

        var itemsHtml = state.items.map(function(item) {
            var skuHtml = item.sku ? '<div class="cart-item__sku">Маркировка: ' + item.sku + '</div>' : '';
            return '<div class="cart-item" data-product-id="' + item.product_id + '">' +
                '<div class="cart-item__info">' +
                '<div class="cart-item__title">' + item.title + '</div>' +
                skuHtml +
                '</div>' +
                '<div class="cart-item__qty">' + item.quantity + ' шт.</div>' +
                '<div class="cart-item__price">' + formatPrice(item.subtotal) + ' тг</div>' +
                '<button type="button" class="cart-item__remove button-plain" data-action="remove" data-product-id="' + item.product_id + '">Удалить</button>' +
                '</div>';
        }).join('');

        var orderFormHtml = '' +
            '<form class="cart-order-form" data-role="order-form">' +
            '<div class="cart-order-form__title">Оформление заказа</div>' +
            '<div class="input-box">' +
            '<i class="icon-fio"></i>' +
            '<input type="text" name="name" class="input-box__input" required autocomplete="off" placeholder="ФИО">' +
            '</div>' +
            '<div class="input-box">' +
            '<i class="icon-phone-border"></i>' +
            '<input type="text" name="phone" class="input-box__input is-phone" required autocomplete="off" placeholder="Телефон">' +
            '</div>' +
            '<div class="input-box">' +
            '<i class="icon-email"></i>' +
            '<input type="email" name="email" class="input-box__input" autocomplete="off" placeholder="E-mail (по желанию)">' +
            '</div>' +
            '<div class="input-box">' +
            '<textarea name="comment" class="input-box__input cart-order-form__comment" rows="3" placeholder="Комментарий к заказу"></textarea>' +
            '</div>' +
            '<div class="form-box__button">' +
            '<button class="button" type="submit"><i class="icon-hand"></i><span>Оформить заказ</span></button>' +
            '</div>' +
            '<div class="form-box__message" data-role="form-message"></div>' +
            '</form>';

        container.innerHTML =
            '<div class="box-modal__title"><i class="icon-basket"></i>Корзина</div>' +
            '<div class="cart-items">' + itemsHtml + '</div>' +
            '<div class="cart-summary">' +
            '<div class="cart-summary__row"><span>Товаров:</span><span>' + state.total_quantity + ' шт.</span></div>' +
            '<div class="cart-summary__row cart-summary__row--total"><span>Сумма:</span><span>' + formatPrice(state.total_amount) + ' тг</span></div>' +
            '</div>' +
            '<div class="cart-actions">' +
            '<button type="button" class="button-plain cart-clear-button" data-action="clear-cart">Очистить корзину</button>' +
            '</div>' +
            orderFormHtml;
    }

    function updateCartUI(state) {
        updateCartCounters(state);
        renderCartModal(state);
        bindCartModalEvents();
        initMasks();
    }

    function fetchCart() {
        return fetch('/api/cart/', {
                credentials: 'same-origin'
            })
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Не удалось получить корзину');
                }
                return response.json();
            })
            .then(function(data) {
                if (!data || data.success === false) {
                    throw new Error(data && data.message ? data.message : 'Ошибка корзины');
                }
                cartState = data;
                updateCartUI(cartState);
                return cartState;
            })
            .catch(function(error) {
                console.error('Ошибка загрузки корзины:', error);
                // Возвращаем пустую корзину при ошибке
                cartState = {
                    items: [],
                    total_quantity: 0,
                    total_amount: '0.00'
                };
                updateCartUI(cartState);
                return cartState;
            });
    }

    function addToCart($btn, quantity) {
        var productData = extractProductData($btn);
        if (!productData.productId || !productData.title) {
            console.warn('Недостаточно данных товара для добавления в корзину.');
            // Показываем уведомление пользователю
            alert('Ошибка: не удалось определить данные товара. Попробуйте обновить страницу.');
            return;
        }
        fetch('/api/cart/items/', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    product_id: productData.productId,
                    title: productData.title,
                    sku: productData.sku,
                    price: productData.price,
                    quantity: quantity || 1
                })
            })
            .then(function(response) {
                if (!response.ok) {
                    return response.json().catch(function() {
                        return {
                            success: false,
                            message: 'Не удалось добавить товар.'
                        };
                    }).then(function(data) {
                        throw data;
                    });
                }
                return response.json();
            })
            .then(function(data) {
                if (data.success === false) {
                    throw data;
                }
                cartState = data;
                updateCartUI(cartState);
            })
            .catch(function(error) {
                console.error('Ошибка добавления в корзину:', error);
                var message = 'Не удалось добавить товар в корзину.';
                if (error && error.message) {
                    message = error.message;
                }
                alert(message);
            });
    }

    function removeFromCart(productId) {
        if (!productId) {
            return;
        }
        fetch('/api/cart/items/remove/', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    product_id: productId
                })
            })
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Не удалось удалить товар.');
                }
                return response.json();
            })
            .then(function(data) {
                if (data.success === false) {
                    throw new Error(data.message || 'Ошибка при удалении товара.');
                }
                cartState = data;
                updateCartUI(cartState);
            })
            .catch(function(error) {
                console.error(error);
            });
    }

    function clearCart() {
        fetch('/api/cart/clear/', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                }
            })
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Не удалось очистить корзину.');
                }
                return response.json();
            })
            .then(function(data) {
                cartState = data;
                updateCartUI(cartState);
            })
            .catch(function(error) {
                console.error(error);
            });
    }

    function bindCartModalEvents() {
        $('#dev_cart_ajax')
            .off('click.cartRemove')
            .on('click.cartRemove', '[data-action="remove"]', function() {
                var productId = $(this).data('productId');
                removeFromCart(productId);
            })
            .off('click.cartClear')
            .on('click.cartClear', '[data-action="clear-cart"]', function() {
                clearCart();
            })
            .off('submit.cartOrder')
            .on('submit.cartOrder', '[data-role="order-form"]', function(event) {
                event.preventDefault();
                handleOrderSubmit(this);
            });
    }

    function handleOrderSubmit(formEl) {
        if (cartState.total_quantity === 0) {
            renderFormMessage(formEl, 'Корзина пуста.', false);
            return;
        }
        if ($(formEl).hasClass('is-loading')) {
            return;
        }

        var formData = new FormData(formEl);
        var payload = {
            name: (formData.get('name') || '').trim(),
            phone: (formData.get('phone') || '').trim(),
            email: (formData.get('email') || '').trim(),
            comment: (formData.get('comment') || '').trim(),
        };

        if (!payload.name) {
            renderFormMessage(formEl, 'Укажите имя.', false);
            return;
        }

        if (!payload.phone && !payload.email) {
            renderFormMessage(formEl, 'Укажите телефон или email.', false);
            return;
        }

        $(formEl).addClass('is-loading');
        renderFormMessage(formEl, '', true);

        fetch('/api/orders/', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify(payload)
            })
            .then(function(response) {
                if (!response.ok) {
                    return response.json().catch(function() {
                        return {
                            success: false,
                            message: 'Не удалось оформить заказ.'
                        };
                    }).then(function(data) {
                        throw data;
                    });
                }
                return response.json();
            })
            .then(function(data) {
                renderFormMessage(formEl, data.message || 'Заказ оформлен. Мы свяжемся с вами.', true);
                formEl.reset();
                $(formEl).removeClass('is-loading');
                fetchCart();
            })
            .catch(function(error) {
                var message = 'Не удалось оформить заказ. Попробуйте позже.';
                if (error && error.message) {
                    message = error.message;
                }
                renderFormMessage(formEl, message, false);
                $(formEl).removeClass('is-loading');
            });
    }

    function initAddToCartButtons() {
        $(document).off('click.cartAdd', '.dev_to_cart').on('click.cartAdd', '.dev_to_cart', function(event) {
            event.preventDefault();
            var $btn = $(this);
            var $box = $btn.closest('.product-box');
            var quantityInput = $box.find('.product-count');
            if (!quantityInput.length) {
                quantityInput = $btn.closest('.product-box').find('input[type=\"number\"]');
            }
            var quantity = parseInt(quantityInput.val(), 10);
            if (isNaN(quantity) || quantity <= 0) {
                quantity = parseInt($btn.data('quantity') || 1, 10);
            }
            if (isNaN(quantity) || quantity <= 0) {
                quantity = 1;
            }
            addToCart($btn, quantity);
        });
    }

    function bindCartOpeners() {
        $(document).off('click.cartOpen', '[data-open="dev_modal_cart"]').on('click.cartOpen', '[data-open="dev_modal_cart"]', function() {
            fetchCart();
        });
    }

    function initQuantityControls() {
        $(document)
            .off('click.qtyIncrease', '.button-qty[data-action=\"increase\"]').on('click.qtyIncrease', '.button-qty[data-action=\"increase\"]', function() {
                var $button = $(this);
                var $productBox = $button.closest('.product-box');
                // Ищем input в правильном порядке: сначала в том же контейнере с кнопками
                var $input = $button.siblings('input[type=\"number\"].product-count').first();
                if (!$input.length) {
                    // Если не нашли, ищем в том же product-box__qty
                    $input = $button.closest('.product-box__qty').find('input.product-count').first();
                }
                if (!$input.length) {
                    // Последний fallback - ищем в product-box
                    $input = $productBox.find('input.product-count').first();
                }
                if ($input.length) {
                    var current = parseInt($input.val(), 10) || 1;
                    $input.val(Math.min(current + 1, 999)).trigger('change');
                }
            })
            .off('click.qtyDecrease', '.button-qty[data-action=\"decrease\"]').on('click.qtyDecrease', '.button-qty[data-action=\"decrease\"]', function() {
                var $button = $(this);
                var $productBox = $button.closest('.product-box');
                // Ищем input в правильном порядке: сначала в том же контейнере с кнопками
                var $input = $button.siblings('input[type=\"number\"].product-count').first();
                if (!$input.length) {
                    // Если не нашли, ищем в том же product-box__qty
                    $input = $button.closest('.product-box__qty').find('input.product-count').first();
                }
                if (!$input.length) {
                    // Последний fallback - ищем в product-box
                    $input = $productBox.find('input.product-count').first();
                }
                if ($input.length) {
                    var current = parseInt($input.val(), 10) || 1;
                    $input.val(Math.max(current - 1, 1)).trigger('change');
                }
            })
            .off('change.qtyInput', '.product-count')
            .on('change.qtyInput', '.product-count', function() {
                var value = parseInt($(this).val(), 10) || 1;
                if (value < 1) {
                    value = 1;
                }
                if (value > 999) {
                    value = 999;
                }
                $(this).val(value);
            });
    }

    function initCart() {
        bindCartModalEvents();
        initAddToCartButtons();
        bindCartOpeners();
        fetchCart();
    }

    function initProductDetail() {
        $(document).off('click.productDetail', '.dev_product_detail').on('click.productDetail', '.dev_product_detail', function(event) {
            event.preventDefault();
            var $link = $(this);
            var productId = $link.data('id');

            if (!productId) {
                console.warn('Не указан ID товара');
                return;
            }

            var $modal = $('#dev_modal_product');
            var $modalContent = $('#dev_modal_product_ajax');

            if (!$modal.length) {
                console.warn('Модальное окно для товара не найдено');
                return;
            }

            // Показываем индикатор загрузки
            $modalContent.html('<div class="text-center" style="padding: 40px;"><i class="icon-loading"></i> Загрузка...</div>');

            // Инициализируем модальное окно, если еще не инициализировано
            var modal = null;
            if (window.Foundation && typeof Foundation.getPlugin === 'function') {
                modal = Foundation.getPlugin($modal, 'Reveal');
            }
            if (!modal) {
                modal = new Foundation.Reveal($modal);
            }

            // Открываем модальное окно
            modal.open();

            // Загружаем детали товара
            $.ajax({
                url: '/api/product/detail/',
                method: 'GET',
                data: {
                    id: productId
                },
                success: function(data) {
                    $modalContent.html(data);

                    // Инициализируем Foundation для нового контента
                    if (window.Foundation) {
                        $(document).foundation();
                    }

                    // Инициализируем контролы количества и кнопку добавления в корзину
                    initQuantityControls();
                    initAddToCartButtons();
                },
                error: function(xhr, status, error) {
                    console.error('Ошибка загрузки товара:', error);
                    $modalContent.html('<div class="callout alert">Не удалось загрузить информацию о товаре. Попробуйте позже.</div>');
                }
            });
        });
    }

    // Обработчик ошибок загрузки изображений - предотвращает запросы к несуществующим файлам
    // Устанавливаем обработчик до загрузки DOM, чтобы перехватить все ошибки
    $(document).on('error', 'img', function(e) {
        var $img = $(this);
        var src = $img.attr('src');
        // Если изображение пытается загрузить product-placeholder.png, заменяем на data URI
        if (src && (src.indexOf('product-placeholder.png') !== -1 || src.indexOf('/static/img/product-placeholder') !== -1)) {
            e.preventDefault();
            e.stopPropagation();
            $img.attr('src', 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==');
            $img.attr('onerror', null); // Удаляем обработчик onerror, если он есть
            return false;
        }
    });

    // Также перехватываем установку onerror атрибутов
    var originalSetAttribute = Element.prototype.setAttribute;
    Element.prototype.setAttribute = function(name, value) {
        if (name === 'onerror' && typeof value === 'string' && value.indexOf('product-placeholder.png') !== -1) {
            // Заменяем product-placeholder.png на data URI
            value = value.replace(/product-placeholder\.png/g, 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==');
        }
        return originalSetAttribute.call(this, name, value);
    };

    $(document).ready(function() {
        initFoundation();
        initWOW();
        initMasks();
        initBenefitsSlider();
        initCanvasClose();
        initFancybox();
        initLeadForms();
        initFaq();
        initCatalogMenu();
        // Инициализируем переключение категорий после меню, но до smooth scroll
        initCategoryToggle();
        // Smooth scroll инициализируем после category toggle, чтобы избежать конфликтов
        initSmoothScroll();
        initQuantityControls();
        initCart();
        initProductDetail();
        initCallbackForm();

        // Обработчик для открытия модальных окон через data-open
        $(document).on('click', '[data-open]', function(e) {
            e.preventDefault();
            e.stopPropagation();
            var modalId = $(this).data('open');
            if (!modalId) {
                return;
            }

            var $modal = $('#' + modalId);
            if (!$modal.length) {
                console.error('Modal not found:', modalId);
                return;
            }

            // Сохраняем текущую позицию прокрутки
            var scrollTop = $(window).scrollTop();
            $('body').data('scroll-top', scrollTop);

            // Пробуем открыть через Foundation
            if (window.Foundation) {
                try {
                    var modal = null;
                    if (typeof Foundation.getPlugin === 'function') {
                        modal = Foundation.getPlugin($modal, 'Reveal');
                    }

                    if (!modal) {
                        modal = new Foundation.Reveal($modal);
                    }

                    if (modal && typeof modal.open === 'function') {
                        // Foundation Sites сам управляет состоянием body
                        modal.open();
                        return;
                    }
                } catch (err) {
                    console.warn('Foundation error, using fallback:', err);
                }
            }

            // Fallback: показываем модальное окно напрямую
            $modal.addClass('is-open').show();
            $('body').addClass('is-reveal-open').css('overflow', 'hidden');

            // Создаем overlay если его нет
            if (!$('.reveal-overlay').length) {
                $('body').append('<div class="reveal-overlay"></div>');
            }
            $('.reveal-overlay').addClass('is-open').show();
        });

        // Функция для восстановления состояния страницы (общая)
        function restorePageState() {
            // Foundation Sites сам управляет состоянием, но мы помогаем восстановить прокрутку
            setTimeout(function() {
                // Убираем служебные классы, если Foundation их не убрал
                $('body').removeClass('is-reveal-open section-products-open');
                $('html').removeClass('is-reveal-open');

                // Прячем overlay, если он вдруг остался висеть
                $('.reveal-overlay').removeClass('is-open').hide();

                // Принудительно скрываем модальные окна, которые могли зависнуть в состоянии is-open
                $('.reveal.is-open').each(function() {
                    var $modal = $(this);
                    $modal.removeClass('is-open').hide();
                });

                // Восстанавливаем прокрутку, если она была заблокирована
                if ($('body').css('overflow') === 'hidden') {
                    $('body').css('overflow', '');
                }
                if ($('html').css('overflow') === 'hidden') {
                    $('html').css('overflow', '');
                }
            }, 100);
        }

        // Обработчик для закрытия модальных окон
        $(document).on('click', '[data-close]', function(e) {
            e.preventDefault();
            var $modal = $(this).closest('.reveal');
            if (!$modal.length) {
                return;
            }

            // Пробуем закрыть через Foundation
            if (window.Foundation && typeof Foundation.getPlugin === 'function') {
                try {
                    var modal = Foundation.getPlugin($modal, 'Reveal');
                    if (modal && typeof modal.close === 'function') {
                        modal.close();
                        restorePageState();
                        return;
                    }
                } catch (err) {
                    console.warn('Foundation close error:', err);
                }
            }

            // Fallback: закрываем напрямую
            $modal.removeClass('is-open').hide();
            $('.reveal-overlay').removeClass('is-open').hide();

            // Восстанавливаем состояние страницы
            restorePageState();
        });

        // Закрытие по клику на overlay
        $(document).on('click', '.reveal-overlay', function(e) {
            if ($(e.target).hasClass('reveal-overlay')) {
                $('.reveal.is-open').each(function() {
                    var $modal = $(this);
                    if (window.Foundation && typeof Foundation.getPlugin === 'function') {
                        try {
                            var modal = Foundation.getPlugin($modal, 'Reveal');
                            if (modal && typeof modal.close === 'function') {
                                modal.close();
                                restorePageState();
                                return;
                            }
                        } catch (err) {
                            // Ignore
                        }
                    }
                    $modal.removeClass('is-open').hide();
                });
                $('.reveal-overlay').removeClass('is-open').hide();

                // Восстанавливаем состояние страницы
                restorePageState();
            }
        });

        // Закрытие по ESC
        $(document).on('keydown', function(e) {
            if (e.keyCode === 27) { // ESC
                $('.reveal.is-open').each(function() {
                    var $modal = $(this);
                    if (window.Foundation && typeof Foundation.getPlugin === 'function') {
                        try {
                            var modal = Foundation.getPlugin($modal, 'Reveal');
                            if (modal && typeof modal.close === 'function') {
                                modal.close();
                                restorePageState();
                                return;
                            }
                        } catch (err) {
                            // Ignore
                        }
                    }
                    $modal.removeClass('is-open').hide();
                });
                $('.reveal-overlay').removeClass('is-open').hide();

                // Восстанавливаем состояние страницы
                restorePageState();
            }
        });

        // Глобальная "страховка" от зависшего состояния после модалок:
        // если нет открытых модальных окон, но страница всё ещё заблокирована,
        // при любом клике выполняем восстановление.
        $(document).on('click.globalRestore touchend.globalRestore', function() {
            if (!$('.reveal.is-open').length) {
                restorePageState();
            }
        });

        // Инициализируем счетчик оставшихся товаров
        updateRemainingCount();

        // Кнопка "Показать еще"
        $('#load-more-products').off('click.loadMore').on('click.loadMore', function() {
            var $hiddenItems = $('.product-item:hidden');
            var itemsToShow = Math.min(24, $hiddenItems.length);

            $hiddenItems.slice(0, itemsToShow).fadeIn(300);

            if ($hiddenItems.length <= itemsToShow) {
                $(this).hide();
            } else {
                updateRemainingCount();
            }

            updateProductsCount();
        });
    });

    function updateProductsCount() {
        // Функция больше не нужна, так как текст заменен на "Смотреть каталог"
        // Оставляем пустую функцию для совместимости
    }

    function updateRemainingCount() {
        var $hiddenItems = $('.product-item:hidden');
        var remaining = $hiddenItems.length;
        $('#remaining-count').text(remaining);

        if (remaining === 0) {
            $('#load-more-products').hide();
        }
    }

    function initCallbackForm() {
        // Общая функция для обработки форм
        function handleFormSubmit(formId, modalId) {
            $(formId).off('submit.form').on('submit.form', function(e) {
                e.preventDefault();
                var $form = $(this);
                var $button = $form.find('button[type="submit"]');
                var originalText = $button.html();

                // Валидация
                var nameField = $form.find('input[type="text"][name="name"]');
                var phoneField = $form.find('input[type="tel"][name="phone"]');
                var messageField = $form.find('textarea[name="message"]');
                var checkbox = $form.find('input[type="checkbox"][required]');

                var name = nameField.val().trim();
                var phone = phoneField.val().trim();
                var message = messageField.length ? messageField.val().trim() : '';

                if (!name) {
                    alert('Пожалуйста, введите ваше имя');
                    nameField.focus();
                    return;
                }

                if (!phone || phone.length < 10) {
                    alert('Пожалуйста, введите корректный номер телефона');
                    phoneField.focus();
                    return;
                }

                // Проверка обязательного сообщения для формы обратной связи
                if (formId === '#feedback_form' && !message) {
                    alert('Пожалуйста, введите сообщение');
                    messageField.focus();
                    return;
                }

                // Проверка чекбокса согласия
                if (checkbox.length && !checkbox.is(':checked')) {
                    alert('Необходимо согласие на обработку персональных данных');
                    return;
                }

                // Блокируем кнопку
                $button.prop('disabled', true).html('<i class="icon-loading"></i> Отправка...');

                // Отправляем форму как form-data (не JSON)
                $.ajax({
                    url: $form.attr('action'),
                    method: 'POST',
                    data: $form.serialize(),
                    headers: {
                        'X-CSRFToken': $form.find('[name=csrfmiddlewaretoken]').val()
                    },
                    success: function(response) {
                        if (response.success) {
                            // Показываем сообщение об успехе
                            $form.html('<div class="alert alert-success" style="padding: 20px; text-align: center;"><i class="icon-check"></i><br>Спасибо! Мы свяжемся с вами в ближайшее время.</div>');

                            // Закрываем модальное окно через 1.5 секунды (как в оригинале)
                            setTimeout(function() {
                                var $modal = $(modalId);

                                // Закрываем через Foundation
                                if (window.Foundation && typeof Foundation.getPlugin === 'function') {
                                    try {
                                        var modal = Foundation.getPlugin($modal, 'Reveal');
                                        if (modal && typeof modal.close === 'function') {
                                            modal.close();
                                        }
                                    } catch (err) {
                                        // Ignore
                                    }
                                }

                                // Fallback: закрываем напрямую
                                $modal.removeClass('is-open').hide();
                                $('.reveal-overlay').removeClass('is-open').hide();

                                // Восстанавливаем состояние (Foundation должен это сделать сам, но на всякий случай)
                                restorePageState();
                            }, 1500);
                        } else {
                            alert(response.message || 'Произошла ошибка при отправке формы');
                            $button.prop('disabled', false).html(originalText);
                        }
                    },
                    error: function(xhr) {
                        var errorMsg = 'Произошла ошибка при отправке формы. Попробуйте еще раз.';
                        if (xhr.responseJSON) {
                            if (xhr.responseJSON.message) {
                                errorMsg = xhr.responseJSON.message;
                            } else if (xhr.responseJSON.error) {
                                errorMsg = xhr.responseJSON.error;
                            }
                        }
                        alert(errorMsg);
                        $button.prop('disabled', false).html(originalText);
                    }
                });
            });
        }

        // Инициализируем все формы
        handleFormSubmit('#callback_form', '#dev_modal_callback');
        handleFormSubmit('#feedback_form', '#dev_modal_feedback');
        handleFormSubmit('#consultation_form', '#dev_modal_consultation');
    }
})(jQuery);